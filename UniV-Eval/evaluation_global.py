# -*- coding: utf-8 -*-

from __future__ import annotations
import asyncio
from datetime import datetime
import os
import glob
import time
import cv2

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
from agents import (
    Runner,
    set_tracing_disabled,
)
from json_repair import repair_json

import base64
import io
import json
from PIL import Image
from typing import Dict, Any, List, Union


# =========================
# User Configuration / 用户配置
# =========================

# 输入案例根目录：每个子文件夹会被当作一个 case 处理。
# Input case root directory: each subfolder is processed as one case.
ROOT_DIR = "input"

# 输出结果目录：保存原始评估结果和格式化后的评估结果。
# Output directory: stores raw evaluation results and formatted evaluation results.
OUTPUT_DIR = "output"

# 每个 case 里原始视频、生成视频、编辑指令文本的文件名；生成视频文件名只是示例，可按实际文件名修改。
# File names for each case; the generated video file name is only an example and can be changed.
ORIGINAL_VIDEO_FILENAME = "source.mp4"
GENERATED_VIDEO_FILENAME = "final_video_t2i_i2v_0.mp4"
EDIT_INSTRUCTION_FILENAME = "reference_method.txt"

# 参考图匹配规则：会在每个 case 文件夹下查找这些后缀。
# Reference image matching patterns: these extensions are searched in each case folder.
REFERENCE_IMAGE_PATTERNS = ["*.jpeg", "*.jpg", "*.png"]

# 视频抽帧参数：FPS 越高、分辨率和质量越高，模型输入成本越大。
# Video frame extraction settings: higher FPS, resolution, and quality increase model input cost.
FPS = 4.0
TARGET_SHORT_SIDE = 480
JPEG_QUALITY = 85

# 模型配置选择：当前 MODEL_FAMILY_MAP 里只有 "seed"。
# Model configuration selector: currently MODEL_FAMILY_MAP only contains "seed".
MODEL_FAMILY = "seed"


from customized_agents_evaluation import (
    itv2v_global_evaluation_agent,
    v2v_global_evaluation_agent,
    it2v_global_evaluation_agent,
    t2v_global_evaluation_agent,
    extract_global_information_agent,
)
from api_master import(
    SEED_RUN_CONFIG,
)


def read_from_text(file_path: str) -> str:
    """
    从指定路径读取文本文件内容。
    Read text file content from the specified path.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return str(content)
    except FileNotFoundError:
        print(f"错误: 文件未找到 -> {file_path}")
        return ""
    except UnicodeDecodeError:
        print("警告: 文件不是UTF-8编码，尝试用GBK重新读取...")
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
            return content
        except Exception as e:
            print(f"读取失败: {e}")
            return ""


def image_to_base64(
    image_source: Union[str, Path, Image.Image],
    image_format: str = None,
    direct: bool = False,
) -> str:
    """
    将图片（文件路径、Path对象或PIL.Image对象）转换为Base64编码的Data URI。
    Convert an image path, Path object, or PIL.Image object to a Base64 data URI.
    """
    if isinstance(image_source, (str, Path)):
        if direct:
            with open(image_source, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")

        if not os.path.exists(image_source):
            raise FileNotFoundError(f"文件未找到: {image_source}")

        if image_format is None:
            if isinstance(image_source, Path):
                extension = image_source.suffix
            else:
                _, extension = os.path.splitext(image_source)

            if not extension:
                raise ValueError("无法从文件路径推断图片格式，请提供 image_format 参数。")
            image_format = extension.lstrip(".").lower()

        if image_format != "jpeg":
            image_format = "jpeg"
            image = Image.open(image_source).convert("RGB")
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            buffer.seek(0)
            encoded_string = base64.b64encode(buffer.read()).decode("utf-8")
        else:
            with open(image_source, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

    elif isinstance(image_source, Image.Image):
        if image_format is None:
            image_format = "png"

        save_format = "jpeg" if image_format.lower() == "jpg" else image_format.lower()
        buffer = io.BytesIO()
        image_source.save(buffer, format=save_format.upper())
        encoded_string = base64.b64encode(buffer.getvalue()).decode("utf-8")

    else:
        raise TypeError("输入 'image_source' 必须是文件路径 (str, pathlib.Path) 或 PIL.Image.Image 对象。")

    mime_type = "jpeg" if image_format.lower() == "jpg" else image_format.lower()
    return f"data:image/{mime_type};base64,{encoded_string}"


def extract_frames_to_base64(
    video_path: str,
    fps: float = 2.0,
    target_short_side: int = 720,
    jpeg_quality: int = 85,
) -> List[Dict[str, Any]]:
    """
    从视频中抽取帧并转换为base64格式。
    Extract frames from a video and convert them to Base64 image inputs.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")

    original_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / original_fps

    if duration >= 10:
        if target_short_side > 480:
            target_short_side = 480
        if fps > 4:
            fps = 4
    if duration >= 15 and fps > 2:
        fps = 2
    if duration >= 90 and fps > 1:
        fps = 1
    if duration >= 180 and target_short_side > 360:
        target_short_side = 360
    if duration >= 300 and fps > 0.5:
        fps = 0.5

    frame_interval = int(original_fps / fps)
    if frame_interval < 1:
        frame_interval = 1
        print("警告: 抽帧频率过高，调整为每帧抽取")

    content_list = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            timestamp = frame_count / original_fps
            h, w, _ = frame.shape
            short_side = min(h, w)

            if short_side > target_short_side:
                scale_factor = target_short_side / short_side
                new_w = int(w * scale_factor)
                new_h = int(h * scale_factor)
                resized_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            else:
                resized_frame = frame

            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
            _, buffer = cv2.imencode(".jpeg", resized_frame, encode_param)
            frame_base64 = base64.b64encode(buffer).decode("utf-8")

            content_list.append({
                "type": "input_text",
                "text": f"[{timestamp:.2f} second]",
            })
            content_list.append({
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{frame_base64}",
            })

        frame_count += 1

    cap.release()
    return content_list

import builtins
original_print = builtins.print
# 定义新的 print 函数，覆盖内置 print。
# Define a timestamped print function that overrides the built-in print.
def print(*args, **kwargs):
    # 获取当前时间并格式化（带毫秒）。
    # Get the current time and format it with milliseconds.
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    # 在输出内容前添加时间戳，然后调用原生 print。
    # Prefix the output with a timestamp, then call the original print.
    original_print(f"[{current_time}]", *args, **kwargs)
set_tracing_disabled(disabled=True)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True)

MODEL_FAMILY_MAP = {
    "seed": SEED_RUN_CONFIG,
}
global_run_config = MODEL_FAMILY_MAP[MODEL_FAMILY]


async def global_evaluation(
    og_video_path: str = None, 
    gene_video_path: str = None,
    image_paths: str = None,
    edit_instrcution_path: str = None
):
    gene_video_frames_content = extract_frames_to_base64(
            video_path=gene_video_path,
            fps=FPS,
            target_short_side=TARGET_SHORT_SIDE,
            jpeg_quality=JPEG_QUALITY
        )
    if og_video_path and gene_video_path and image_paths and edit_instrcution_path: #  i+t+v to v / 图像+文本+视频到视频
        og_video_frames_content = extract_frames_to_base64(
            video_path=og_video_path,
            fps=FPS,
            target_short_side=TARGET_SHORT_SIDE,
            jpeg_quality=JPEG_QUALITY
        )
        evaluation_content = []
        for idx, image_path in enumerate(image_paths, start=1):
            ref_image = image_to_base64(image_path)
            evaluation_content.append({"type": "input_text", "text": f"The following is ReferenceImage {idx}:"})
            evaluation_content.append({"type": "input_image", "image_url": ref_image})
        edit_instruction = read_from_text(edit_instrcution_path)
        evaluation_content.append({"type": "input_text", "text": f"This is the user's EditInstruction: {edit_instruction}."})
        evaluation_content.append({"type": "input_text", "text": "The following is OriginalVideo:"})
        evaluation_content.extend(og_video_frames_content)
        evaluation_content.append({"type": "input_text", "text": "The following is GenerationVideo:"})
        evaluation_content.extend(gene_video_frames_content)
        messages = [ {"role": "user", "content": evaluation_content} ]
        print("Message constructed, preparing for model evaluation...")
        response = await Runner.run(itv2v_global_evaluation_agent, messages, run_config=global_run_config)
        result_str = response.final_output.strip()
        input_tokens = response.context_wrapper.usage.input_tokens 
        output_tokens = response.context_wrapper.usage.output_tokens 
        print(result_str)
        print(f"input_tokens: {input_tokens}, output_tokens: {output_tokens}")
    if not og_video_path and gene_video_path and image_paths and edit_instrcution_path: # i+t to v / 图像+文本到视频
        edit_instruction = read_from_text(edit_instrcution_path)
        evaluation_content = []
        for idx, image_path in enumerate(image_paths, start=1):
            ref_image = image_to_base64(image_path)
            evaluation_content.append({"type": "input_text", "text": f"The following is ReferenceImage {idx}:"})
            evaluation_content.append({"type": "input_image", "image_url": ref_image})
        evaluation_content.append({"type": "input_text", "text": f"This is the user's EditInstruction: {edit_instruction}."})
        evaluation_content.append({"type": "input_text", "text": "The following is GenerationVideo:"})
        evaluation_content.extend(gene_video_frames_content)
        messages = [ {"role": "user", "content": evaluation_content} ]
        print("Message constructed, preparing for model evaluation...")
        response = await Runner.run(it2v_global_evaluation_agent, messages, run_config=global_run_config)
        result_str = response.final_output.strip()
        input_tokens = response.context_wrapper.usage.input_tokens 
        output_tokens = response.context_wrapper.usage.output_tokens 
        print(result_str)
        print(f"input_tokens: {input_tokens}, output_tokens: {output_tokens}")
    if not og_video_path and gene_video_path and not image_paths and edit_instrcution_path: # t to v / 文本到视频
        edit_instruction = read_from_text(edit_instrcution_path)
        evaluation_content = []
        evaluation_content.append({"type": "input_text", "text": f"This is the user's EditInstruction: {edit_instruction}."})
        evaluation_content.append({"type": "input_text", "text": "The following is GenerationVideo:"})
        evaluation_content.extend(gene_video_frames_content)
        messages = [ {"role": "user", "content": evaluation_content} ]
        print("Message constructed, preparing for model evaluation...")
        response = await Runner.run(t2v_global_evaluation_agent, messages, run_config=global_run_config)
        result_str = response.final_output.strip()
        input_tokens = response.context_wrapper.usage.input_tokens 
        output_tokens = response.context_wrapper.usage.output_tokens 
        print(result_str)
        print(f"input_tokens: {input_tokens}, output_tokens: {output_tokens}")
    if og_video_path and gene_video_path and not image_paths and not edit_instrcution_path: # v to v / 视频到视频
        og_video_frames_content = extract_frames_to_base64(
            video_path=og_video_path,
            fps=FPS,
            target_short_side=TARGET_SHORT_SIDE,
            jpeg_quality=JPEG_QUALITY
        )
        evaluation_content = []
        evaluation_content.append({"type": "input_text", "text": "The following is OriginalVideo:"})
        evaluation_content.extend(og_video_frames_content)
        evaluation_content.append({"type": "input_text", "text": "The following is GenerationVideo:"})
        evaluation_content.extend(gene_video_frames_content)
        messages = [ {"role": "user", "content": evaluation_content} ]
        print("Message constructed, preparing for model evaluation...")
        response = await Runner.run(v2v_global_evaluation_agent, messages, run_config=global_run_config)
        result_str = response.final_output.strip()
        input_tokens = response.context_wrapper.usage.input_tokens 
        output_tokens = response.context_wrapper.usage.output_tokens 
        print(result_str)
        print(f"input_tokens: {input_tokens}, output_tokens: {output_tokens}")

    return result_str


async def extract_global_information(global_result: str) -> dict:
    """
    将 Prompt 发送给 LLM，并获取、解析返回的结构化信息。
    Send the prompt to the LLM, then retrieve and parse the structured output.
    """
    try:
        print("--- Agent is processing structured output... ---")
        evaluation_content = []
        evaluation_content.append({"type": "input_text", "text": f"The following is the raw evaluation output: {global_result}"})
        messages = [ {"role": "user", "content": evaluation_content} ]

        response = await Runner.run(extract_global_information_agent, messages, run_config=global_run_config)
        result_str = response.final_output.strip()
        print("--- Structured output processing completed ---")
        return result_str
    
    except json.JSONDecodeError:
        print("Error: Unable to parse JSON returned by LLM. Raw output:")
        print(result_str)
        return {"error": "LLM did not return valid JSON.", "raw_output": result_str}
    except Exception as e:
        print(f"Error occurred while interacting with LLM: {e}")
        raise


def evaluation_main():
    total_start = time.perf_counter()
    case_dirs = [
        os.path.join(ROOT_DIR, d)
        for d in os.listdir(ROOT_DIR)
        if os.path.isdir(os.path.join(ROOT_DIR, d))
    ]

    print(f"Detected {len(case_dirs)} cases, starting processing...\n")

    for case_dir in case_dirs:
        case_start = time.perf_counter()
        case_name = os.path.basename(case_dir)

        og_video_path = os.path.join(case_dir, ORIGINAL_VIDEO_FILENAME)
        gene_video_path = os.path.join(case_dir, GENERATED_VIDEO_FILENAME)
        edit_instruction_path = os.path.join(case_dir, EDIT_INSTRUCTION_FILENAME)

        ref_image_paths = []
        for ext in REFERENCE_IMAGE_PATTERNS:
            ref_image_paths.extend(glob.glob(os.path.join(case_dir, ext)))

        if not os.path.exists(og_video_path):
            print(f"Original video not found: {og_video_path}")
            og_video_path = ""
            
        if not os.path.exists(gene_video_path):
            print(f"Generated video not found: {gene_video_path}")
            gene_video_path = ""
            
        if not ref_image_paths:
            print(f"Reference images not found: {ref_image_paths}")
            ref_image_paths = ""
            
        if not os.path.exists(edit_instruction_path):
            print(f"Edit instruction not found: {edit_instruction_path}")
            edit_instruction_path = ""
            

        print(f"Found original video: {og_video_path}")
        print(f"Found generated video: {gene_video_path}")

        RAW_OUTPUT_PATH = os.path.join(OUTPUT_DIR, f"{case_name}_eval.json")
        FORMAT_OUTPUT_PATH = os.path.join(OUTPUT_DIR, f"{case_name}_format_eval.json")
        try:
            print("Starting global evaluation...")
            result_str = asyncio.run(global_evaluation(og_video_path, gene_video_path, ref_image_paths, edit_instruction_path))
            print("Evaluation completed, checking JSON format...")

            try:
                repaired_result = repair_json(result_str, ensure_ascii=False)
                result_json = json.loads(repaired_result)
                print("result_str is valid JSON format after repair.")
                with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
                    json.dump(result_json, f, ensure_ascii=False, indent=4)
                print(f"Result saved to: {os.path.abspath(RAW_OUTPUT_PATH)}")

            except json.JSONDecodeError as e:
                print(f"result_str is not valid JSON format after repair, error: {e}")
                error_path = RAW_OUTPUT_PATH.replace(".json", "_raw.txt")
                with open(error_path, "w", encoding="utf-8") as f:
                    f.write(result_str)
                print(f"Raw result saved to: {os.path.abspath(error_path)}")
            
            format_result_str = asyncio.run(extract_global_information(result_str))
            with open(FORMAT_OUTPUT_PATH, "w", encoding="utf-8") as f:
                json.dump(format_result_str, f, ensure_ascii=False, indent=4)
            print(f"Formatted result saved to: {os.path.abspath(FORMAT_OUTPUT_PATH)}")

        except Exception as e:
            print(f"An exception occurred during execution: {e}")
            continue
        case_elapsed = time.perf_counter() - case_start
        print(f"Case runtime: {case_elapsed:.2f}s")
        print("---------------------------------------------------------------------------")

    total_elapsed = time.perf_counter() - total_start
    print(f"\nAll cases processed. Total runtime: {total_elapsed:.2f}s")


if __name__ == "__main__":
    evaluation_main()

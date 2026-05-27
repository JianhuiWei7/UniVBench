# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import cv2
from agents import Agent, Runner, set_tracing_disabled

from api_master import get_seed_run_config


# =========================
# User Configuration / 用户配置
# =========================

# 输入视频目录：脚本会递归查找其中的视频文件。
# Input video directory: the script recursively searches for video files in it.
INPUT_DIR = "input"

# 输出 JSONL 文件：每一行保存一个视频的 V2T 结果。
# Output JSONL file: each line stores one video's V2T result.
OUTPUT_FILE = "output/v2t_baseline_results.jsonl"

# 视频文件匹配后缀。
# Video file extensions to process.
VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv", ".webm"]

# V2T 抽帧参数：旧 baseline 使用 2 fps。
# V2T frame extraction settings: the old baseline used 2 fps.
V2T_FPS = 2.0
TARGET_SHORT_SIDE = 480
JPEG_QUALITY = 85

# V2T 使用的视觉模型配置；如需改模型名，改这里即可。
# Vision model config for V2T; change the model name here if needed.
V2T_MODEL_NAME = "doubao-seed-1-6-vision-250815"
V2T_TEMPERATURE = 0.0001
V2T_MAX_TOKENS = 32768


V2T_BASELINE_PROMPT_EN = """
I will provide you with a video, which may be multi-shot or single-shot. Based on the video, a detailed, logically coherent video script will be created, strictly following the requirements below to ensure comprehensive content coverage and clear depiction of dynamic processes.
1. Requirements for Core Element Coverage (Mandatory, Expandable)
The script must fully include the following eight core elements, with specific detailed descriptions for each element (no generalizations allowed):
Video Style and Atmosphere: Specify the overall style (e.g., Realistic style, Lolita style, 2D animation style, Japanese Ukiyo-e style, retro film style, etc.) and emotional atmosphere (e.g., warm, tense, tranquil).
Subject Details: Provide a detailed description of the video subject (character/object/scene) in terms of external features, such as the material of a character's clothing, the texture of an object, or the decorative details of a scene.
Subject Actions: Break down the subject's continuous actions and mark key action nodes (e.g., "raise hand -> pick up object -> turn around").
Background Information: Specify the background scene (e.g., "study room/street/indoor living room") and background details (e.g., "books on the bookshelf/Chinese parasols by the street/sofa in the living room").
Color Parameters: Clarify the saturation (e.g., "high saturation/low saturation/medium saturation"), hue (e.g., "warm yellow tone/cool blue tone/neutral gray tone"), and contrast (e.g., "high contrast/low contrast/soft contrast").
Lighting Setup: Explain the lighting direction (e.g., "frontal light/side light/backlight/top light"), lighting effect (e.g., "soft light/hard light/diffused light"), and brightness level (e.g., "bright/dim/softly bright").
Camera Parameters: Define the shot type (e.g., "wide shot/medium shot/close-up/extreme close-up"), camera movement (e.g., "push-in/pull-out/pan/follow shot"), camera height and angle (e.g., "eye-level/top-down/low-angle"), shooting technique (e.g., "slow-motion/time-lapse/normal shooting"), camera perspective (e.g., "first-person view/third-person view/God's-eye view"), and depth of field (e.g., "deep depth of field/shallow depth of field/medium depth of field").
Relative Position: Mark the subject's position in the video frame (e.g., "1/3 from the left/center of the frame/lower right corner"), the subject's position relative to the camera (e.g., "directly in front of the camera/left of the camera/diagonally behind the camera"), and the relative positions between multiple subjects (e.g., "Subject A is 2 meters to the left of Subject B/Subject C is in front of Subject D").
2. Requirements for Capturing Dynamic Changes
When dynamic adjustments occur in the above elements, the change process must be clearly recorded. For example:
Shot Type Change: The medium shot gradually zooms in to an extreme close-up.
Lighting Change: The softly bright (frontal soft light) shifts to dim (side backlight with hard light).
Position Change: The subject moves from the center of the frame to 1/3 from the right.
3. Script Quality Requirements
Detail Completeness: Each core element must be described specifically, avoiding "vague expressions" (e.g., instead of "relatively bright lighting", use "bright lighting with frontal soft light and high-saturation warm yellow tone").
Logical Coherence: The subject's actions, camera movements, and element changes must conform to real-world logic.
Content Richness: The video script should be as detailed and content-rich as possible.
4. Shot Transition Requirements
Shot Transition Keyword: When a shot transition occurs, the keyword "[Shot cut]" must be used to separate two shots. For example: The video opens with a [certain style], first depicting [content]; Shot cut, then [content]; Shot cut, and finally [content].
Description of New Shots: When a new shot appears, the content of the new shot must be described, including all core elements and the capture of dynamic changes. If the subject has appeared in previous shots, references can be used.
5. Output Format Requirements
Please directly output a coherent video script.
"""


v2t_agent = Agent(
    name="v2t baseline agent",
    instructions="You are a helpful video understanding assistant.",
)

v2t_run_config = get_seed_run_config(
    model_name=V2T_MODEL_NAME,
    temperature=V2T_TEMPERATURE,
    max_tokens=V2T_MAX_TOKENS,
)

set_tracing_disabled(disabled=True)


def get_videos(input_dir: str | Path) -> List[Path]:
    """
    递归查找输入目录下的视频文件。
    Recursively find video files under the input directory.
    """
    root = Path(input_dir)
    if not root.exists():
        raise FileNotFoundError(f"Input directory does not exist: {root}")

    videos = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    ]
    return sorted(videos)


def extract_frames_to_base64(
    video_path: str | Path,
    fps: float = V2T_FPS,
    target_short_side: int = TARGET_SHORT_SIDE,
    jpeg_quality: int = JPEG_QUALITY,
) -> List[Dict[str, Any]]:
    """
    从视频中抽取帧并转换为模型可用的 Base64 输入。
    Extract frames from a video and convert them to Base64 model inputs.
    """
    video_path = str(video_path)
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Unable to open video file: {video_path}")

    original_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if original_fps <= 0:
        cap.release()
        raise ValueError(f"Unable to read FPS from video file: {video_path}")

    duration = total_frames / original_fps
    if duration >= 10:
        target_short_side = min(target_short_side, 480)
        fps = min(fps, 4)
    if duration >= 15:
        fps = min(fps, 2)
    if duration >= 90:
        fps = min(fps, 1)
    if duration >= 180:
        target_short_side = min(target_short_side, 360)
    if duration >= 300:
        fps = min(fps, 0.5)

    frame_interval = max(int(original_fps / fps), 1)
    content_list: List[Dict[str, Any]] = []
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
                frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
            _, buffer = cv2.imencode(".jpeg", frame, encode_param)
            frame_base64 = base64.b64encode(buffer).decode("utf-8")

            content_list.append({"type": "input_text", "text": f"[{timestamp:.2f} second]"})
            content_list.append({
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{frame_base64}",
            })

        frame_count += 1

    cap.release()
    return content_list


async def v2t(video_path: str | Path) -> str:
    """
    对单个视频执行 V2T baseline，输出详细视频脚本。
    Run the V2T baseline on one video and return a detailed video script.
    """
    video_content = extract_frames_to_base64(video_path)
    user_inputs = [{"type": "input_text", "text": V2T_BASELINE_PROMPT_EN}]
    user_inputs.extend(video_content)
    messages = [{"role": "user", "content": user_inputs}]

    result = await Runner.run(v2t_agent, messages, run_config=v2t_run_config)
    return result.final_output.strip()


def load_processed_videos(output_file: str | Path) -> set[str]:
    """
    读取已处理视频，避免重复处理。
    Load processed video names to avoid duplicate work.
    """
    output_path = Path(output_file)
    if not output_path.exists():
        return set()

    processed = set()
    with output_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "video_filename" in item:
                processed.add(item["video_filename"])
    return processed


async def run_batch(input_dir: str | Path, output_file: str | Path) -> None:
    """
    批量处理输入目录下的视频，并将结果写入 JSONL。
    Process videos in a directory and write results to JSONL.
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    video_paths = get_videos(input_dir)
    processed_videos = load_processed_videos(output_path)
    videos_to_process = [path for path in video_paths if path.name not in processed_videos]

    print(f"Total videos found: {len(video_paths)}")
    print(f"Already processed: {len(processed_videos)}")
    print(f"Videos to process: {len(videos_to_process)}")

    for video_path in videos_to_process:
        try:
            print(f"Processing: {video_path}")
            model_output = await v2t(video_path)
            result_item = {
                "video_filename": video_path.name,
                "video_path": str(video_path),
                "generated_script": model_output,
            }
            with output_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(result_item, ensure_ascii=False) + "\n")
            print(f"Saved: {video_path.name}")
        except Exception as e:
            print(f"Error processing {video_path}: {e}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run V2T baseline on videos.")
    parser.add_argument("--input-dir", default=INPUT_DIR, help="Directory containing videos.")
    parser.add_argument("--output-file", default=OUTPUT_FILE, help="JSONL output file path.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_batch(args.input_dir, args.output_file))

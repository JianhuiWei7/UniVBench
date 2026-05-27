# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
from datetime import datetime
import json
import os
import sys
import io
from pathlib import Path
from typing import Any

from agents import Runner, set_tracing_disabled
from json_repair import repair_json

from api_master import SEED_RUN_CONFIG
from customized_agents_evaluation import v2t_evaluation_agent


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


# =========================
# User Configuration / 用户配置
# =========================

# 输入 case 根目录：每个子文件夹会被当作一个 V2T evaluation case 处理。
# Input case root directory: each subfolder is processed as one V2T evaluation case.
ROOT_DIR = "input_v2t_eval"

# 输出结果目录：保存 V2T 文本评估结果。
# Output directory: stores V2T text evaluation results.
OUTPUT_DIR = "output_v2t_eval"

# 每个 case 里的 GT JSON/文本和模型输出文本文件名。
# File names for GT JSON/text and model output text in each case.
GT_TEXT_FILENAME = "gt.json"
MODEL_OUTPUT_FILENAME = "generated_script.txt"

# 模型配置选择：当前 MODEL_FAMILY_MAP 里只有 "seed"。
# Model configuration selector: currently MODEL_FAMILY_MAP only contains "seed".
MODEL_FAMILY = "seed"


MODEL_FAMILY_MAP = {
    "seed": SEED_RUN_CONFIG,
}
global_run_config = MODEL_FAMILY_MAP[MODEL_FAMILY]


import builtins

original_print = builtins.print


# 定义新的 print 函数，覆盖内置 print。
# Define a timestamped print function that overrides the built-in print.
def print(*args, **kwargs):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    original_print(f"[{current_time}]", *args, **kwargs)


set_tracing_disabled(disabled=True)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True)


def read_text_file(file_path: str | Path) -> str:
    """
    读取文本文件，优先使用 UTF-8，失败时回退到 GBK。
    Read a text file with UTF-8 first, then fall back to GBK.
    """
    file_path = Path(file_path)
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="gbk")


def read_gt_input(file_path: str | Path) -> Any:
    """
    读取 GT 输入：如果是合法 JSON，则返回 JSON 对象；否则返回原始文本。
    Read GT input: return a JSON object if valid, otherwise return raw text.
    """
    raw_text = read_text_file(file_path)
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return raw_text


async def evaluate_v2t_text(gt_text: Any, model_output: str) -> str:
    """
    调用 v2t_evaluation_agent，对 GT 和模型输出文本进行语义匹配评估。
    Run v2t_evaluation_agent to compare GT and model output semantically.
    """
    evaluation_content = [
        {
            "type": "input_text",
            "text": (
                "Ground truth JSON/text:\n"
                f"{json.dumps(gt_text, ensure_ascii=False, indent=2) if not isinstance(gt_text, str) else gt_text}\n\n"
                "Model output text:\n"
                f"{model_output}"
            ),
        }
    ]
    messages = [{"role": "user", "content": evaluation_content}]

    print("Message constructed, preparing for V2T text evaluation...")
    response = await Runner.run(v2t_evaluation_agent, messages, run_config=global_run_config)
    result_str = response.final_output.strip()
    input_tokens = response.context_wrapper.usage.input_tokens
    output_tokens = response.context_wrapper.usage.output_tokens
    print(f"input_tokens: {input_tokens}, output_tokens: {output_tokens}")
    return result_str


def save_result(result_str: str, raw_output_path: str | Path) -> None:
    """
    保存模型输出；优先用 repair_json 修复后保存为 .json，否则保存为 _raw.txt。
    Save model output as JSON after repair_json when possible, otherwise save it as _raw.txt.
    """
    raw_output_path = Path(raw_output_path)
    try:
        repaired_result = repair_json(result_str, ensure_ascii=False)
        result_json = json.loads(repaired_result)
        raw_output_path.write_text(
            json.dumps(result_json, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
        print(f"Result saved to: {raw_output_path.resolve()}")
    except json.JSONDecodeError as e:
        print(f"Result is not valid JSON, error: {e}")
        error_path = raw_output_path.with_name(raw_output_path.stem + "_raw.txt")
        error_path.write_text(result_str, encoding="utf-8")
        print(f"Raw result saved to: {error_path.resolve()}")


def evaluation_main():
    """
    批量执行 V2T 文本评估。
    Run V2T text evaluation in batch.

    Expected case structure / 期望的 case 结构:
    input_v2t_eval/
      case_001/
        gt.json
        generated_script.txt
      case_002/
        gt.json
        generated_script.txt
    """
    total_start = datetime.now()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    case_dirs = [
        Path(ROOT_DIR) / d
        for d in os.listdir(ROOT_DIR)
        if (Path(ROOT_DIR) / d).is_dir()
    ]

    print(f"Detected {len(case_dirs)} cases, starting V2T text evaluation...\n")

    for case_dir in case_dirs:
        case_name = case_dir.name
        gt_text_path = case_dir / GT_TEXT_FILENAME
        model_output_path = case_dir / MODEL_OUTPUT_FILENAME
        raw_output_path = Path(OUTPUT_DIR) / f"{case_name}_v2t_eval.json"

        if not gt_text_path.exists():
            print(f"GT file not found, skipping case: {gt_text_path}")
            continue

        if not model_output_path.exists():
            print(f"Model output file not found, skipping case: {model_output_path}")
            continue

        try:
            print(f"Starting V2T text evaluation for case: {case_name}")
            gt_text = read_gt_input(gt_text_path)
            model_output = read_text_file(model_output_path)
            result_str = asyncio.run(evaluate_v2t_text(gt_text, model_output))
            save_result(result_str, raw_output_path)
        except Exception as e:
            print(f"An exception occurred during case {case_name}: {e}")
            continue

        print("---------------------------------------------------------------------------")

    elapsed = datetime.now() - total_start
    print(f"\nAll cases processed. Total runtime: {elapsed}")


if __name__ == "__main__":
    evaluation_main()

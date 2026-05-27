# UniV-Eval 全局视频评估

<p align="center">
  <b>语言 / Language</b>:
  <a href="./README.md">English</a> |
  <a href="./README.zh-CN.md">简体中文</a>
</p>

`UniV-Eval` 是一个用于批量评估视频生成结果的轻量工具。主入口是 `evaluation_global.py`：它会遍历输入目录下的每个 case，读取视频、参考图和文本指令，抽取视频帧，组装成多模态消息，然后调用评估 Agent 输出质量检查结果和结构化评分。

## 1. 文件说明

当前核心文件如下：

```text
evaluation_global.py
baseline_V2T.py
V2T_evaluation.py
customized_agents_evaluation.py
api_master.py
requirements.txt
README.md
README.zh-CN.md
README.en.md
```

说明：

- `evaluation_global.py`：主入口文件，包含用户配置、视频抽帧、输入组装、批量运行和结果保存逻辑。
- `baseline_V2T.py`：V2T baseline，输入视频，输出详细的视频文本脚本。
- `V2T_evaluation.py`：V2T 文本评估入口，输入 GT JSON/文本和模型输出文本，评估模型输出对 GT 的覆盖程度。
- `customized_agents_evaluation.py`：全局视频评估相关的 Agent 定义。
- `api_master.py`：模型运行配置，例如 Seed、OpenAI、Azure OpenAI、Gemini 的 RunConfig。
- `requirements.txt`：当前代码需要的 Python 依赖。

## 2. 安装依赖

建议使用 Python 3.10 或更高版本。

在项目根目录执行：

```bash
pip install -r requirements.txt
```

如果你的内部环境中 `agents` SDK 的安装方式不同，请按内部环境要求安装或切换到对应运行环境。

## 3. 设置环境变量

当前 `evaluation_global.py` 默认使用 `seed` 模型配置，因此必须设置：

```bash
export SEED_API_KEY="your_seed_api_key"
```

`api_master.py` 中也保留了 OpenAI、Azure OpenAI 和 Gemini 的运行配置。如果你后续要扩展 `MODEL_FAMILY_MAP` 使用这些模型，可以按需设置：

```bash
export OPENAI_API_KEY="your_openai_api_key"
export AZURE_OPENAI_API_KEY="your_azure_openai_api_key"
export GEMINI_API_KEY="your_gemini_api_key"
```

## 4. 准备输入目录

默认输入目录是 `input`，默认输出目录是 `output`。可以先创建：

```bash
mkdir -p input output
```

每个 case 是 `input` 下的一个子文件夹。示例：

```text
input/
  case_001/
    source.mp4
    final_video_t2i_i2v_0.mp4
    reference_method.txt
    ref_01.jpg
    ref_02.png
  case_002/
    source.mp4
    my_generated_video.mp4
    reference_method.txt
```

默认文件含义：

- `source.mp4`：原始视频。缺失时，脚本会尝试进入不需要原始视频的评估模式。
- `final_video_t2i_i2v_0.mp4`：生成视频文件名示例。生成视频是核心输入，文件名可以改，但必须和配置中的 `GENERATED_VIDEO_FILENAME` 一致。
- `reference_method.txt`：编辑指令文本。缺失时，脚本会尝试进入不需要文本指令的评估模式。
- `*.jpeg`、`*.jpg`、`*.png`：参考图。缺失时，脚本会尝试进入不需要参考图的评估模式。

## 5. 修改用户配置

打开 `evaluation_global.py`，在顶部找到 `User Configuration / 用户配置` 区域：

```python
ROOT_DIR = "input"
OUTPUT_DIR = "output"

ORIGINAL_VIDEO_FILENAME = "source.mp4"
GENERATED_VIDEO_FILENAME = "final_video_t2i_i2v_0.mp4"
EDIT_INSTRUCTION_FILENAME = "reference_method.txt"

REFERENCE_IMAGE_PATTERNS = ["*.jpeg", "*.jpg", "*.png"]

FPS = 4.0
TARGET_SHORT_SIDE = 480
JPEG_QUALITY = 85

MODEL_FAMILY = "seed"
```

常用配置说明：

- `ROOT_DIR`：输入 case 根目录。
- `OUTPUT_DIR`：结果输出目录。
- `ORIGINAL_VIDEO_FILENAME`：每个 case 中原始视频的文件名。
- `GENERATED_VIDEO_FILENAME`：每个 case 中生成视频的文件名。当前值只是示例，可以改成你的实际文件名。
- `EDIT_INSTRUCTION_FILENAME`：每个 case 中编辑指令文本的文件名。
- `REFERENCE_IMAGE_PATTERNS`：参考图匹配规则。
- `FPS`：每秒抽取多少帧。
- `TARGET_SHORT_SIDE`：抽帧图片短边目标尺寸。
- `JPEG_QUALITY`：抽帧图片 JPEG 质量。
- `MODEL_FAMILY`：模型配置选择。当前入口默认只映射 `"seed"`。

抽帧参数越高，模型输入越大，耗时和成本也会增加。

## 6. 运行视频生成结果评估

确认环境变量、输入目录和配置都准备好后，在项目根目录执行：

```bash
python evaluation_global.py
```

程序会自动处理 `ROOT_DIR` 下的所有 case。

## 7. 运行 V2T baseline

`baseline_V2T.py` 用于评估视频理解能力的第一步：输入视频，生成详细的视频脚本描述。

默认配置在文件顶部：

```python
INPUT_DIR = "input"
OUTPUT_FILE = "output/v2t_baseline_results.jsonl"
VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
V2T_FPS = 2.0
TARGET_SHORT_SIDE = 480
JPEG_QUALITY = 85
V2T_MODEL_NAME = "doubao-seed-1-6-vision-250815"
```

运行方式：

```bash
python baseline_V2T.py --input-dir input --output-file output/v2t_baseline_results.jsonl
```

输出是 JSONL，每一行对应一个视频：

```json
{
  "video_filename": "example.mp4",
  "video_path": "input/example.mp4",
  "generated_script": "The video ..."
}
```

## 8. 运行 V2T 文本评估

`V2T_evaluation.py` 用于第二步：比较 GT JSON/文本和 V2T baseline 生成的文本脚本，判断 GT 中的元素是否被模型输出覆盖。

默认输入结构：

```text
input_v2t_eval/
  case_001/
    gt.json
    generated_script.txt
  case_002/
    gt.json
    generated_script.txt
```

其中：

- `gt.json`：GT checklist / GT JSON，也可以是普通文本。对于 Hugging Face 数据集，它对应的是数据集中 `full_list/<case_id>/caption.json` 里面 `json` 这个键的值。
- `generated_script.txt`：V2T baseline 或其他模型生成的视频文本描述。

运行方式：

```bash
python V2T_evaluation.py
```

默认输出目录：

```text
output_v2t_eval/
```

每个 case 会输出：

```text
case_name_v2t_eval.json
```

评估结果会对 GT 中的每个原子元素输出：

```json
{
  "item": "...",
  "is_present": "True/False",
  "score": "1, 0.5 or 0",
  "reasoning": "..."
}
```

脚本会使用 `repair_json` 尝试修复模型输出，并用 `ensure_ascii=False` 保存中文。

## 9. 视频生成结果评估输出

每个 case 会在 `OUTPUT_DIR` 下生成：

```text
case_name_eval.json
case_name_format_eval.json
```

说明：

- `*_eval.json`：主评估 Agent 的原始 JSON 输出。
- `*_format_eval.json`：结构化评分 Agent 处理后的评分结果。

如果模型原始输出不是合法 JSON，会保存为：

```text
case_name_eval_raw.txt
```

## 10. 支持的评估模式

脚本会根据每个 case 中实际存在的文件自动选择模式：

- (RV2V + TV2V)图像 + 文本 + 视频到视频：有原始视频、生成视频、参考图和编辑指令。
- (R2V)图像 + 文本到视频：有生成视频、参考图和编辑指令，无原始视频。
- (T2V)文本到视频：有生成视频和编辑指令，无原始视频和参考图。
- (V2V)视频到视频：有原始视频和生成视频，无参考图和编辑指令。

V2T 相关流程是独立脚本：

- `baseline_V2T.py`：视频到文本。
- `V2T_evaluation.py`：文本和 GT 文本/GT JSON 的语义匹配评估。

## 11. 主流程

视频生成结果评估流程：

```text
读取用户配置
  -> 扫描 input 下的 case 文件夹
  -> 检查每个 case 中存在的输入文件
  -> 对生成视频和可选原始视频抽帧
  -> 将视频帧和参考图转为 Base64
  -> 组装多模态模型消息
  -> 根据输入组合选择对应评估 Agent
  -> 调用模型生成原始评估结果
  -> 保存原始评估结果
  -> 调用结构化评分 Agent
  -> 保存格式化评分结果
```

V2T baseline 和评估流程：

```text
准备视频文件
  -> baseline_V2T.py 抽帧并生成 generated_script
  -> 准备 gt.json 和 generated_script.txt
  -> V2T_evaluation.py 调用 v2t_evaluation_agent
  -> repair_json 修复评估结果
  -> 保存 V2T 文本评估 JSON
```

## 12. 常见问题

如果看到 `ARK_API_KEY environment variable not set`，请确认已经设置：

```bash
export SEED_API_KEY="your_seed_api_key"
```

如果某个 case 运行失败，请优先检查：

- `GENERATED_VIDEO_FILENAME` 是否和真实生成视频文件名一致。
- 生成视频是否真的存在于 case 文件夹中。
- `ROOT_DIR` 和 `OUTPUT_DIR` 是否配置正确。
- 抽帧参数是否过高导致输入过大。
- 如果 V2T 文本评估结果不是合法 JSON，脚本会先尝试 `repair_json`；修复失败时会保存为 raw 文本。

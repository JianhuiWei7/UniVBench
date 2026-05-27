# UniV-Eval Global Video Evaluation

<p align="center">
  <b>Language</b>:
  <a href="./README.md">English</a> |
  <a href="./README.zh-CN.md">简体中文</a>
</p>

`UniV-Eval` is a lightweight tool for batch evaluation of generated videos. The main entry point is `evaluation_global.py`: it scans case folders, reads videos, reference images, and text instructions, extracts video frames, builds multimodal messages, and calls evaluation agents to produce quality inspection results and structured scores.

## 1. Files

Core files:

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

Descriptions:

- `evaluation_global.py`: Main entry file. It contains user configuration, frame extraction, input construction, batch execution, and result saving logic.
- `baseline_V2T.py`: V2T baseline. It takes videos as input and generates detailed video scripts.
- `V2T_evaluation.py`: V2T text evaluation entry. It compares GT JSON/text with model output text and evaluates coverage.
- `customized_agents_evaluation.py`: Agent definitions required for global video evaluation.
- `api_master.py`: Model run configurations, such as Seed, OpenAI, Azure OpenAI, and Gemini RunConfig definitions.
- `requirements.txt`: Python dependencies required by the current code.

## 2. Install Dependencies

Python 3.10 or later is recommended.

Run from the project root:

```bash
pip install -r requirements.txt
```

If your internal environment installs the `agents` SDK differently, install or activate the matching runtime according to your internal instructions.

## 3. Set Environment Variables

`evaluation_global.py` uses the `seed` model family by default, so this environment variable is required:

```bash
export SEED_API_KEY="your_seed_api_key"
```

`api_master.py` also keeps OpenAI, Azure OpenAI, and Gemini run configs. If you later extend `MODEL_FAMILY_MAP` to use them, set the corresponding keys as needed:

```bash
export OPENAI_API_KEY="your_openai_api_key"
export AZURE_OPENAI_API_KEY="your_azure_openai_api_key"
export GEMINI_API_KEY="your_gemini_api_key"
```

## 4. Prepare Input Folders

The default input directory is `input`, and the default output directory is `output`. Create them first:

```bash
mkdir -p input output
```

Each subfolder under `input` is one evaluation case. Example:

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

Default file meanings:

- `source.mp4`: Original video. If missing, the script tries to use an evaluation mode that does not require an original video.
- `final_video_t2i_i2v_0.mp4`: Example generated video file name. The generated video is the core input; the file name can be changed, but it must match `GENERATED_VIDEO_FILENAME`.
- `reference_method.txt`: Edit instruction text. If missing, the script tries to use an evaluation mode that does not require text instructions.
- `*.jpeg`, `*.jpg`, `*.png`: Reference images. If missing, the script tries to use an evaluation mode that does not require reference images.

## 5. Edit User Configuration

Open `evaluation_global.py` and find the `User Configuration / 用户配置` section near the top:

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

Common settings:

- `ROOT_DIR`: Root directory containing case folders.
- `OUTPUT_DIR`: Directory where results are saved.
- `ORIGINAL_VIDEO_FILENAME`: Original video file name in each case.
- `GENERATED_VIDEO_FILENAME`: Generated video file name in each case. The current value is only an example and can be changed to your actual file name.
- `EDIT_INSTRUCTION_FILENAME`: Edit instruction text file name in each case.
- `REFERENCE_IMAGE_PATTERNS`: Reference image matching patterns.
- `FPS`: Number of frames sampled per second.
- `TARGET_SHORT_SIDE`: Target short-side size for sampled frames.
- `JPEG_QUALITY`: JPEG quality for sampled frames.
- `MODEL_FAMILY`: Model configuration selector. The current entry maps only `"seed"` by default.

Higher frame extraction settings increase model input size, runtime, and cost.

## 6. Run Generated Video Evaluation

After environment variables, input folders, and configuration are ready, run:

```bash
python evaluation_global.py
```

The script automatically processes all cases under `ROOT_DIR`.

## 7. Run V2T Baseline

`baseline_V2T.py` is the first step for evaluating video understanding: it takes videos as input and generates detailed video scripts.

Default settings are near the top of the file:

```python
INPUT_DIR = "input"
OUTPUT_FILE = "output/v2t_baseline_results.jsonl"
VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
V2T_FPS = 2.0
TARGET_SHORT_SIDE = 480
JPEG_QUALITY = 85
V2T_MODEL_NAME = "doubao-seed-1-6-vision-250815"
```

Run:

```bash
python baseline_V2T.py --input-dir input --output-file output/v2t_baseline_results.jsonl
```

The output is JSONL, one line per video:

```json
{
  "video_filename": "example.mp4",
  "video_path": "input/example.mp4",
  "generated_script": "The video ..."
}
```

## 8. Run V2T Text Evaluation

`V2T_evaluation.py` is the second step: it compares GT JSON/text with the V2T generated script and checks whether GT elements are covered by the model output.

Default input structure:

```text
input_v2t_eval/
  case_001/
    gt.json
    generated_script.txt
  case_002/
    gt.json
    generated_script.txt
```

Where:

- `gt.json`: GT checklist / GT JSON. Plain text is also supported. For the Hugging Face dataset, it corresponds to the value of the `json` field in `full_list/<case_id>/caption.json` in the dataset.
- `generated_script.txt`: Video script generated by V2T baseline or another model.

Run:

```bash
python V2T_evaluation.py
```

Default output directory:

```text
output_v2t_eval/
```

Each case writes:

```text
case_name_v2t_eval.json
```

The evaluation result checks each atomic GT element and outputs:

```json
{
  "item": "...",
  "is_present": "True/False",
  "score": "1, 0.5 or 0",
  "reasoning": "..."
}
```

The script uses `repair_json` to repair model output when possible and saves Chinese text with `ensure_ascii=False`.

## 9. Generated Video Evaluation Outputs

For each case, the script writes:

```text
case_name_eval.json
case_name_format_eval.json
```

Descriptions:

- `*_eval.json`: Raw JSON output from the main evaluation agent.
- `*_format_eval.json`: Structured score result produced by the scoring agent.

If the raw model output is not valid JSON, it is saved as:

```text
case_name_eval_raw.txt
```

## 10. Supported Evaluation Modes

The script automatically selects a mode based on which files exist in each case:

- (RV2V + TV2V)Image + text + video to video: original video, generated video, reference images, and edit instruction are present.
- (R2V)Image + text to video: generated video, reference images, and edit instruction are present; original video is missing.
- (T2V)Text to video: generated video and edit instruction are present; original video and reference images are missing.
- (V2V)Video to video: original video and generated video are present; reference images and edit instruction are missing.

V2T is handled by standalone scripts:

- `baseline_V2T.py`: video to text.
- `V2T_evaluation.py`: semantic matching between text and GT text / GT JSON.

## 11. Main Pipeline

Generated video evaluation flow:

```text
Load user configuration
  -> Scan case folders under input
  -> Check available input files in each case
  -> Extract frames from generated video and optional original video
  -> Encode video frames and reference images as Base64
  -> Build multimodal model messages
  -> Select the matching evaluation agent based on input combination
  -> Call the model to generate raw evaluation output
  -> Save raw evaluation output
  -> Call the structured scoring agent
  -> Save formatted score output
```

V2T baseline and evaluation flow:

```text
Prepare video files
  -> baseline_V2T.py extracts frames and generates generated_script
  -> Prepare gt.json and generated_script.txt
  -> V2T_evaluation.py calls v2t_evaluation_agent
  -> repair_json repairs the evaluation result
  -> Save V2T text evaluation JSON
```

## 12. Troubleshooting

If you see `ARK_API_KEY environment variable not set`, make sure this is set:

```bash
export SEED_API_KEY="your_seed_api_key"
```

If a case fails, first check:

- Whether `GENERATED_VIDEO_FILENAME` matches the real generated video file name.
- Whether the generated video actually exists in the case folder.
- Whether `ROOT_DIR` and `OUTPUT_DIR` are configured correctly.
- Whether frame extraction settings are too high and making the model input too large.
- If the V2T text evaluation result is not valid JSON, the script tries `repair_json` first; if repair fails, it saves the raw text.

# UniVBench: Towards Unified Evaluation for Video Foundation Models
> 
> **Official repository for the CVPR 2026 paper: "UniVBench: Towards Unified Evaluation for Video Foundation Models"**.
> 
> We are continuing to update the repo.
> 

<p align="center">
  <a href="https://arxiv.org/abs/2602.21835" target="_blank"><img src="https://img.shields.io/badge/arXiv-2602.21835-red"></a>
  <a href="https://huggingface.co/datasets/JianhuiWei/UniVBench" target="_blank"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Dataset-blue"></a>
</p>

## 💡 About

Video foundation models aim to integrate video understanding, generation, editing, and instruction following within a single framework, making them a central direction for next-generation multimodal systems. 

However, existing evaluation benchmarks remain fragmented and limited in scope, as they each **target a single task, rely on task-specific metrics, and typically use short or simple video clips**. As a result, they do not capture the unified  capabilities that these models are designed to deliver.

## 🚀 Key Contributions

* **Unified Benchmark(UniVBench)**: a multi-task video sources, with 
1. Non-copyright, multi/single-shot, high-quality videos.
2. Detailed video captions (for **T2V, V2T, V2V[reconstruction]** tasks).
3. Text + Reference images for video editing instruction(for **TV2V, RV2V** tasks).
4. Text +  Reference images to video generation (for **R2V** task).
5. Comprehensive image sets.
All curated, verified , and selected manually.


* **Unified Evaluation(UniVEval)**: a multi-task evaluation system, with 
1. Comprehenisve and fine-grained dimensions.
2. Atomic checklist for objective score and interpretability. (textctual feedback for model improvement)
3. Dynamic adaptation to multiple input modality (text, image, video)

* **Evaluation and Video Modeling Alignment**: A principled framework for attributing model capabilities and failures across the perception-generation spectrum. By aligning evaluation with the goals of unified video modeling, our benchmark establishes a foundation for measuring progress toward general-purpose, instruction-following video intelligence.



## 🧠 UniVBench & UniVEval 

<img width="1000" height="710" alt="image" src="https://github.com/JianhuiWei7/UniVBench/blob/main/assest/teaserfigure_UniVBench.png" />

UniVBench is the first unified benchmark designed to evaluate video foundation models across their full capability spectrum. The benchmark comprises **620\* high-quality, multi-shot videos, each with rich annotations including detailed captions, multi-format editing instructions, and reference images**. Crucially, all content is **human-created and copyright-free**, enabling fair evaluation of editing, reconstruction, and instruction-following without legal or data contamination concerns. 

We pair the benchmark with a unified agentic evaluation system (UniV-Eval) that standardizes prompting, instruction parsing, and multi-dimensional scoring across all tasks. This provides **consistent, interpretable metrics** that enable direct cross-model and cross-task comparison, while **supporting fine-grained attribution of errors to perception versus generation components**.

> *\*Note*: The dataset scale has been expanded from 200 samples (in the original paper) to 620.

## 📌 Case Study of UniVEval

<img width="1000" height="710" alt="image" src="https://github.com/JianhuiWei7/UniVBench/blob/main/assest/evaluation_case.jpg" />

**UniV-Eval** introduces a fine-grained, multidimensional evaluation framework. It decomposes "generation performance" into interpretable checklists, enhancing diagnostic capabilities beyond single-score evaluations. This system is compatible with **UniVBench** and standardizes prompting and instruction parsing across tasks, providing consistent evaluation for any input-output combination (video, image, text).

### Evaluation Process
1. **Decomposing and Planning**: Long videos are segmented into clips and further broken down into shot-level units using PySceneDetect. Each clip is paired with reference images and user instructions, forming the basis for evaluation.
   
2. **Shot-Level Fine-Grained Evaluation**: The **shot_evaluation** agent assesses nine major categories (e.g., subject, actions, lighting) with 21 subcategories for detailed feedback. The model's output is compared against the input, identifying specific deficiencies for targeted training. 

Finally, an **evaluation_score agent** aggregates diagnostic results and provides final scores across six evaluation dimensions.


## 📊 Evaluation & Results



## ✍️ Dataset Download

To download the whole UniVBench dataset, run the following command in your terminal:

```bash
python ./download.py
```

## UniVBench Directory Structure

Here is the directory structure for `UniVBench/benchmark` along with descriptions for each folder and file type:

```text
UniVBench/
├── full_list/                             # Complete benchmark data for video editing tasks
│   ├── 1/                                 # Each numbered folder represents a specific test case
│   │   ├── 1.mp4                          # The original source video file
│   │   ├── caption.json                   # Captions for the video **[T2V, V2T, V2V tasks]**
│   │   ├── number_of_shot.txt             # Records the number of shots in the video
│   │   ├── text_editing.txt               # Text editing instructions (original instruction)
│   │   ├── text_editing_en.txt            # English text editing **[TV2V]** instructions (Optimized instruction; English)
│   │   ├── text_editing_cn.txt            # Chinese text editing **[TV2V]** instructions (Optimized instruction; Chinese)
│   │   ├── reference_editing_single/      
│   │   │   ├── reference_editing.txt      # Editing instructions for the single reference image (original instruction)
│   │   │   ├── reference_editing_en.txt   # English editing instructions with single reference image**[RV2V]** (Optimized instruction)
│   │   │   ├── reference_editing_cn.txt   # Chinese editing instructions with single reference image**[RV2V]** (Optimized instruction)
│   │   │   └── reference_image_1.jpeg     
│   │   └── reference_editing_multiple/    # Editing materials directory for multiple reference images
│   │       ├── reference_editing.txt      # Editing instructions for multiple reference images (original instruction)
│   │       ├── reference_editing_en.txt   # English editing instructions with multiple reference images**[RV2V]** (Optimized instruction)
│   │       ├── reference_editing_cn.txt   # Chinese editing instructions with multiple reference images**[RV2V]** (Optimized instruction)
│   │       ├── reference_image_1.png      
│   │       └── reference_image_2.jpeg     
│   ├── 2/
│   │   └── ...
│   └── ... (Contains hundreds of similarly numbered test cases)
│
├── R2V/                                # Data for Reference-to-Video generation tasks **[R2V]**
│   ├── 1/                              # Each numbered folder represents an R2V test case
│   │   ├── R2V_planning.json           # Planning configuration and parameters for the R2V task
│   │   ├── reference_image_0.png       # Reference image 0 used for video generation
│   │   └── reference_image_1.jpeg      # Reference image 1 used for video generation
│   ├── 2/
│   │   └── ...
│   └── ... (Contains hundreds of R2V test cases)
│
└── reference_images_set/               # A categorized repository of reference images
    ├── animals/                        # Reference images of animals
    ├── objects/                        # Reference images of objects
    ├── people/                         # Reference images of people
    ├── plants/                         # Reference images of plants
    └── scenes/                         # Reference images of scenes
```



## 📖 Citation

If you find our work helpful, please consider citing our paper:

```bibtex
@article{wei2026univbench,
  title={UniVBench: Towards Unified Evaluation for Video Foundation Models},
  author={Wei, Jianhui and Zhang, Xiaotian and Li, Yichen and Wang, Yuan and Zhang, Yan and Chen, Ziyi and Tang, Zhihang and Xu, Wei and Liu, Zuozhu},
  journal={arXiv preprint arXiv:2602.21835},
  year={2026}
}

```

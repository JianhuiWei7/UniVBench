# UniVBench: Towards Unified Evaluation for Video Foundation Models
> 
> **Official repository for the CVPR 2026 paper: "UniVBench: Towards Unified Evaluation for Video Foundation Models"**.
> 
> Note: Code and dataset will be available soon.
> 
<a  href="https://arxiv.org/abs/2602.21835"><img src="https://img.shields.io/badge/PaperLink-red.svg?style=for-the-badge"></a>

## 💡 About

Video foundation models aim to integrate video understanding, generation, editing, and instruction following within a single framework, making them a central direction for next-generation multimodal systems. 

However, existing evaluation benchmarks remain fragmented and limited in scope, as they each **target a single task, rely on task-specific metrics, and typically use short or simple video clips**. As a result, they do not capture the unified  capabilities that these models are designed to deliver.

## 🚀 Key Contributions

* **Unified Benchmark**: The first multi-shot video dataset specifically designed for unified evaluation, free of copyright and contamination issues.

* **Unified Evaluation**: A unified agentic evaluation system that enables  measurement across understanding, generation, editing, and reconstruction.

* **Evaluation and Video Modeling Alignment**: A principled framework for attributing model capabilities and failures across the perception-generation spectrum. By aligning evaluation with the goals of unified video modeling, our benchmark establishes a foundation for measuring progress toward general-purpose, instruction-following video intelligence.



## 🧠 UniVBench & UniVEval 

<img width="1000" height="710" alt="image" src="https://github.com/JianhuiWei7/UniVBench/blob/main/assest/teaserfigure_UniVBench.png" />

UniVBench is the first unified benchmark designed to evaluate video foundation models across their full capability spectrum. The benchmark comprises **600 high-quality, multi-shot videos, each with rich annotations including detailed captions, multi-format editing instructions, and reference images**. Crucially, all content is **human-created and copyright-free**, enabling fair evaluation of editing, reconstruction, and instruction-following without legal or data contamination concerns. 

We pair the benchmark with a unified agentic evaluation system (UniV-Eval) that standardizes prompting, instruction parsing, and multi-dimensional scoring across all tasks. This provides **consistent, interpretable metrics** that enable direct cross-model and cross-task comparison, while **supporting fine-grained attribution of errors to perception versus generation components**.

## 📌 Case Study of UniVEval

<img width="1000" height="710" alt="image" src="https://github.com/JianhuiWei7/UniVBench/blob/main/assest/evaluation_case.jpg" />

**UniV-Eval** introduces a fine-grained, multidimensional evaluation framework. It decomposes "generation performance" into interpretable checklists, enhancing diagnostic capabilities beyond single-score evaluations. This system is compatible with **UniVBench** and standardizes prompting and instruction parsing across tasks, providing consistent evaluation for any input-output combination (video, image, text).

### Evaluation Process
1. **Decomposing and Planning**: Long videos are segmented into clips and further broken down into shot-level units using PySceneDetect. Each clip is paired with reference images and user instructions, forming the basis for evaluation.
   
2. **Shot-Level Fine-Grained Evaluation**: The **shot_evaluation** agent assesses nine major categories (e.g., subject, actions, lighting) with 21 subcategories for detailed feedback. The model's output is compared against the input, identifying specific deficiencies for targeted training. 

Finally, an **evaluation_score agent** aggregates diagnostic results and provides final scores across six evaluation dimensions.


## 📊 Evaluation & Results



## ⚙️ Data Synthesis

*(Installation instructions, environment setup, and inference scripts will be updated upon code release.)*

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

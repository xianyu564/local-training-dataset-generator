# 模型微调 / Model Fine-tuning

本项目不仅提供数据生成能力，还包含了一套完整的微调流程，用于训练轻量化且具备推理能力的模型（如 Qwen2.5-0.5B-Instruct）。

This project provides not only data generation but also a complete fine-tuning workflow for training lightweight models with reasoning capabilities (e.g., Qwen2.5-0.5B-Instruct).

## 🚀 概述 / Overview

微调的目标是让模型学习如何理解复杂的代码上下文并生成逻辑严密的推理轨迹。我们采用了参数高效的微调技术 (PEFT)，特别是 LoRA。

The goal of fine-tuning is to enable the model to understand complex code contexts and generate logically sound reasoning traces. We utilize Parameter-Efficient Fine-Tuning (PEFT) techniques, specifically LoRA.

## 🛠️ 环境准备 / Environment Setup

微调脚本位于 `src/fine-tune/` 目录下。

The fine-tuning scripts are located in the `src/fine-tune/` directory.

1.  **安装依赖 / Install Dependencies**:
    ```bash
    pip install -r src/fine-tune/requirements.txt
    ```
    注：推荐在具备 GPU（如 NVIDIA T4/A100）的环境中运行。
    Note: Running in a GPU environment (e.g., NVIDIA T4/A100) is recommended.

2.  **核心组件 / Core Components**:
    *   `train.py`: 基于 Unsloth 的微调主脚本。 The main fine-tuning script based on Unsloth.
    *   `app.py`: 提供 Gradio 界面，支持远程训练、聊天与测试。 A Gradio interface for remote training, chat, and testing.
    *   `export_gguf.py`: 将微调后的 LoRA 权重导出为 GGUF 格式。 Export fine-tuned LoRA weights to GGUF format.

## 📈 训练配置 / Training Configuration

我们在训练中使用了以下关键配置：
We used the following key configurations during training:

*   **基础模型 / Base Model**: Qwen2.5-0.5B-Instruct
*   **训练方法 / Method**: LoRA (Rank 16, Alpha 16)
*   **数据集 / Dataset**: 自动生成的 1,400+ 个高质量样本（包含推理轨迹）。
    1,400+ automatically generated high-quality samples (including reasoning traces).
*   **优化器 / Optimizer**: AdamW (8-bit)

## 🧪 测试与评测 / Testing & Evaluation

训练结束后，系统会自动运行一套测试流程。
After training, the system automatically runs a testing workflow.

### 测试数据 / Test Data
测试集位于 `src/fine-tune/data/`：
*   `test_questions.csv`: 基础测试问题集。
*   `test_questions_fullLength.jsonl`: 包含完整代码上下文的进阶测试集。
*   `test_mapping.md`: 问题与源代码的对应关系。

### 评测结果 / Results
微调后的模型在代码逻辑解释（场景 1）和架构设计方案（场景 2）中表现出明显的推理步数提升。详细的评测报告保存在 `data/6.fine_tune_qwen/test_results.txt`。

The fine-tuned model shows significant improvement in reasoning steps for code logic explanation (Scenario 1) and architectural design (Scenario 2). Detailed evaluation reports are saved in `data/6.fine_tune_qwen/test_results.txt`.

## 📁 产物输出 / Output Artifacts

输出文件保存在 `data/6.fine_tune_qwen/`：
*   `adapter_model.safetensors`: LoRA 权重文件。
*   `adapter_config.json`: 权重配置文件。
*   `qwen2.5-0.5b-instruct.Q8_0.gguf`: 量化后的 GGUF 模型（可选）。

---
更多关于如何运行微调的信息，请参考 `src/fine-tune/README.md`。
For more information on how to run the fine-tuning, please refer to `src/fine-tune/README.md`.

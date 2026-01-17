# 微调验证流程 / Fine-tuning & Validation

本项目包含一个轻量化的微调示例，用于验证生成的“智能训练数据集”是否能有效提升模型在代码分析与架构设计场景下的表现。

This project includes a lightweight fine-tuning example to validate if the generated "Intelligent Training Dataset" effectively improves model performance in code analysis and architectural design scenarios.

## 1. 技术规格 / Technical Specifications

为确保验证的可复现性与效率，我们采用了以下技术配置：
To ensure reproducibility and efficiency, we used the following technical configuration:

- **基础模型 / Base Model**: `Qwen2.5-0.5B-Instruct`
- **训练框架 / Training Framework**: `unsloth` (优化显存占用与训练速度)
- **硬件环境 / Hardware**: Hugging Face Space `T4-small` GPU

## 2. 验证目标 / Validation Goals

- **格式对齐**：验证模型是否能正确输出 `<thought>` 标签包裹的推理轨迹。
- **逻辑一致性**：验证模型在处理本地代码业务逻辑时的推理步骤是否合理。
- **架构感知**：验证模型是否能基于给定的类架构骨架生成符合逻辑的设计方案。

## 2. 快速开始 / Quick Start

### 环境准备 / Preparation
微调部分依赖 `unsloth` 等库，建议在 GPU 环境下运行。
```bash
pip install -r src/fine-tune/requirements.txt
```

### 训练 (LoRA) / Training
```bash
# 脚本会自动寻找 data/5.final_output/ 下的训练集
python src/fine-tune/train.py
```

### 推理测试 / Inference Test
训练完成后，运行评测脚本对预设的 10 个代表性题目进行自动化推理。
```bash
python src/fine-tune/run_inference.py
```
结果将保存在 `lora/test_results_latest.txt` 中。

## 3. 评测题目设计 / Test Case Design

为实事求是地评估效果，测试集包含：
- **基础逻辑题**：测试对函数内部业务规则的提取。
- **复杂设计题**：模拟真实需求，测试在现有类架构上扩展功能的设计能力。

详细的题目与验证集对应关系见 `src/fine-tune/data/test_mapping.md`。

## 4. 产物说明 / Artifacts

- **LoRA Weights**：位于 `lora/qwen2.5-0.5b-lora/`，可被 PEFT 加载。
- **GGUF Model**：支持端侧推理部署。
- **Evaluation Report**：详尽的推理轨迹记录，用于对比微调前后的效果差异。
[demo](https://huggingface.co/xianyu564/train-qwen-demo)
[demo-a](https://huggingface.co/xianyu564/train-qwen-demo-a)
[demo-b](https://huggingface.co/xianyu564/train-qwen-demo-b)
# 本地代码仓的智能训练数据生成与处理 / Intelligent Training Data Generation for Local Repositories

本项目旨在为本地代码仓库构建一个自动化的智能训练数据生成与处理框架，以支持 Qwen 2.5 等系列模型的微调。通过对本地代码进行静态分析、场景化任务生成及 LLM 推理轨迹提取，生成高质量的指令微调数据集。

This project builds an automated framework for generating and processing intelligent training data from local code repositories to support fine-tuning of models like Qwen 2.5. It produces high-quality instruction datasets through static analysis, scenario-based task generation, and LLM reasoning trace extraction.

## 项目背景 / Background

高质量的训练数据是提升模型处理行业特定业务流程与规则能力的关键。本项目针对特定代码仓架构，自动化生成包含推理轨迹（Reasoning Trace）的训练样本，使其具备回答业务逻辑问题及给出架构设计方案的能力。

High-quality training data is key to enhancing a model's ability to handle industry-specific business processes and rules. This project automates the generation of training samples with reasoning traces for specific code architectures, enabling models to answer business logic questions and provide architectural designs.

## 核心任务场景 / Core Scenarios

本项目精准覆盖以下两个核心场景：
This project covers two core scenarios:

- **场景 1：业务流程与规则问答 (QA)**
  - **描述**：根据函数级代码片段，自动生成包含原代码上下文、业务规则提取及推理过程的问答对。
  - **Scenario 1: Business Process & Rule QA**: Generates Q&A pairs based on function-level code snippets, including original code context, business rule extraction, and reasoning.
- **场景 2：基于架构的设计方案生成 (Design)**
  - **描述**：为给定需求生成基于代码仓现有架构的设计方案，并提供详细的解释与推理轨迹。
  - **Scenario 2: Architecture-based Design**: Generates design solutions for specific requirements based on existing repository architecture, providing detailed explanations and reasoning traces.

## 系统架构 / System Architecture

流水线分为四个独立阶段，确保处理的有效性与可扩展性：
The pipeline consists of four independent stages to ensure effectiveness and extensibility:

1.  **代码切片 (Slicing)**：利用 AST 提取函数与类的静态特征（Docstring、复杂度、继承关系等）。
2.  **任务生成 (Scenario Processing)**：基于切片元数据，针对不同场景构建结构化任务 Prompt。
3.  **批处理提交 (Batch Submission)**：使用 OpenAI Batch API 高效获取包含推理轨迹的 LLM 回复。
4.  **数据集编译 (Dataset Compilation)**：将原始回执转换为包含 `<thought>` 标签的微调 JSONL 格式。

## 快速开始 / Quick Start

1.  **环境安装 / Install**：`pip install -r requirements.txt`
2.  **配置密钥 / Configure**：在 `config.json` 中配置 API Key。
3.  **准备源码 / Prepare Repo**：将目标仓库（如以下示例）放入 `data/0.cloned_repo/`。
    - [repo_fastapi_light](https://github.com/nsidnev/fastapi-realworld-example-app.git)
    - [repo_ecommerce_medium](https://github.com/saleor/saleor.git)
    - [repo_iot_special](https://github.com/home-assistant/core.git)
4.  **执行流水线 / Run**：参考 `docs/USAGE.md` 按阶段运行。
5.  **微调验证 / Fine-tune**：参考 `docs/FINETUNE.md` 进行轻量化模型微调验证。

## 模型与演示 / Model & Demo

本项目配套的微调模型、演示界面及测试结果已托管至 Hugging Face：
The fine-tuned models, demo interface, and test results are hosted on Hugging Face:

- **[Hugging Face Space (Interactive Demo)](https://huggingface.co/spaces/xianyu564/train-qwen-demo)**: 在线体验模型推理过程。
- **[Hugging Face Model Repo (Weights & Results)](https://huggingface.co/xianyu564/train-qwen-demo)**: 获取微调后的 LoRA 权重及评测报告。

## 文档索引 / Documentation

- [系统设计与数据结构 / Design & Data Formats](docs/DESIGN.md)
- [使用手册 / Usage Guide](docs/USAGE.md)
- [微调流程说明 / Fine-tuning Guide](docs/FINETUNE.md)
- [处理记录 / Processing Records](docs/RECORDS.md)

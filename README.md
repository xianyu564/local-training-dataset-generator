# Local Training Dataset Generator

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

本项目是一个自动化的代码仓库训练数据集生成器。它能够深入分析本地代码库，并利用 LLM (如 OpenAI GPT) 自动生成高质量、带推理轨迹 (Reasoning Traces) 的微调数据集。

This project is an automated training dataset generator for code repositories. It performs deep analysis of local codebases and leverages LLMs (e.g., OpenAI GPT) to generate high-quality fine-tuning datasets with Reasoning Traces.

## 🎯 我们的想法 / The Idea

现有的代码数据集通常缺乏深度。本项目的核心理念是：
Existing code datasets often lack depth. The core philosophy of this project is:

1.  **从源码提取上下文 / Context Extraction**: 不仅仅是代码片段，还包括类结构、函数关系和复杂度。
    Not just code snippets, but also class structures, function relationships, and complexity.
2.  **生成推理轨迹 / Reasoning Traces**: 让模型学习“如何思考”代码，而不是死记硬背。
    Enabling models to learn "how to think" about code, rather than rote memorization.
3.  **多场景覆盖 / Multi-Scenario Coverage**:
    *   **场景 1 (QA) / Scenario 1**: 针对具体函数，生成资深开发者级别的问答与逻辑推理。
        For specific functions, generating senior developer-level Q&A and logical reasoning.
    *   **场景 2 (Design) / Scenario 2**: 针对类架构，根据新需求生成技术方案与设计决策。
        For class architectures, generating technical solutions and design decisions based on new requirements.

## 🚀 核心工作流 / The Workflow

系统采用模块化的流水线架构：
The system adopts a modular pipeline architecture:

1.  **代码切片 (Slicing)**: 分析 `data/0.cloned_repo` 中的源码，生成结构化的代码片段。
    Analyze source code in `data/0.cloned_repo` to generate structured code slices.
2.  **场景处理 (Processing)**: 将切片转化为 LLM 请求任务。
    Transform slices into LLM request tasks.
3.  **批处理提交 (Submission)**: 利用 OpenAI Batch API 进行低成本大规模生成。
    Leverage OpenAI Batch API for cost-efficient large-scale generation.
4.  **数据集编译 (Compilation)**: 将 LLM 返回的结果重新组合成最终的训练数据集 (JSONL)。
    Recombine LLM responses into the final training dataset (JSONL).

## 📦 示例仓库 / Example Repositories

为了确保生成数据的多样性与代表性，我们选择了三个示例库。详细的处理数量与抽样策略请参考 [处理记录](docs/RECORDS.md)。
We selected three example repositories to ensure data diversity. For detailed processing counts and sampling strategies, please refer to the [Processing Records](docs/RECORDS.md).

*   [**repo_fastapi_light**](https://github.com/nsidnev/fastapi-realworld-example-app.git): 轻量级仓库，用于快速验证流程。 (Lightweight for fast verification)
*   [**repo_ecommerce_medium**](https://github.com/saleor/saleor.git): 中等规模电商项目，代表典型的业务逻辑。 (Medium-scale E-commerce, representing typical business logic)
*   [**repo_iot_special**](https://github.com/home-assistant/core.git): 物联网专项仓库，包含领域特定设计模式。 (Specialized IoT repo with domain-specific patterns) 

这些库分别代表了不同的规模 (Scale) 和 领域 (Domain)。在测试中，我们对大规模仓库进行了抽样处理，并跳过了人工审核环节以实现全自动化。
These repositories represent different scales and domains. In testing, we sampled large-scale repositories and skipped manual review for full automation.

## ✅ 评判标准达成 / Meeting Evaluation Criteria

本项目针对原始需求的评判标准进行了针对性设计：
This project is specifically designed to meet the evaluation criteria of the original requirements:

### 1. 场景覆盖与逻辑正确性 / Scenario Coverage & Logical Correctness
- **双场景支持**: 场景1（函数级QA）和场景2（类级架构设计）完整覆盖代码理解与方案设计两大类需求。
- **逻辑推理链**: 每个训练样本都包含结构化的推理步骤（Reasoning Steps），确保 LLM 输出逻辑的可追溯性。
- **复杂度分层**: 通过启发式算法自动评估代码复杂度（simple/medium/complex），针对不同难度生成差异化问答内容。

### 2. 数据处理的有效性与创新性 / Effectiveness & Innovation
- **自动化全流程**: 从代码克隆到最终数据集生成，无需人工干预（除配置外）。
- **推理轨迹提取**: 利用 `<thought>` 标签结构化封装推理过程，支持 Qwen 2.5 系列模型的 CoT 微调。
- **Batch API 优化**: 采用 OpenAI Batch API 降低 50% 成本，支持大规模并发处理。

### 3. 架构完整性与可扩展性 / Architecture Completeness & Extensibility
- **模块化设计**: 4 个独立的 Stage（Slicing → Processing → Submission → Compilation），易于替换或扩展。
- **配置驱动**: 通过 `config.json` 灵活控制 API 端点、采样策略、并发参数等。
- **多语言支持**: Prompt 模板已支持中英文双语，可轻松扩展至其他自然语言。

### 4. 示例数据的清晰度与合规性 / Clarity & Compliance
- **完整数据流**: `data/` 目录保留从原始代码（0.cloned_repo）到最终输出（5.final_output）的全部中间产物，确保可追溯性。
- **推理 Trace 产出**: 每个训练样本都包含明确的 Reasoning Steps，并在统计报告中显示平均推理深度（Avg Reasoning Steps）。
- **自动化验证**: 微调后模型通过 10 个代表性测试用例验证，结果保存在 `data/6.fine_tune_qwen/test_results.txt`。

## 📁 目录指南 / Directory Guide

*   `src/pipeline/`: 核心逻辑组件（切片器、处理器、提交器、编译器）。 Core logic components.
*   `data/`: 数据流中心（从 0.原始代码 到 5.最终输出）。 Data flow center.

## 🛠️ 开始使用 / Getting Started

1.  **安装依赖 / Install Dependencies**: `pip install -r requirements.txt`
2.  **配置 / Configuration**: 编辑 `config.json` (提供 OpenAI API Key).
3.  **准备源码 / Prepare Source**: 将仓库放入 `data/0.cloned_repo/`.
4.  **运行流水线 / Run Pipeline**: 详见 [使用指南](docs/USAGE.md). See [Usage Guide](docs/USAGE.md).
5.  **模型微调 / Model Fine-tuning**: 详见 [微调指南](docs/FINETUNE.md). See [Fine-tuning Guide](docs/FINETUNE.md).
    *   **Live Demo**: [Hugging Face Space](https://huggingface.co/spaces/xianyu564/train-qwen-demo)

---

📖 详细文档 / Documentation:
- [使用指南 (Usage Guide)](docs/USAGE.md)
- [设计文档 (Design Document)](docs/DESIGN.md)
- [处理记录 (Processing Records)](docs/RECORDS.md)
- [微调指南 (Fine-tuning Guide)](docs/FINETUNE.md)

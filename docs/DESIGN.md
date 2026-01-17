# 系统设计文档 / System Design Document

本文档定义了“本地代码仓智能训练数据生成框架”的技术实现路径，重点阐述如何通过自动化手段生成覆盖业务逻辑与架构设计、且包含详尽推理轨迹（Reasoning Trace）的高质量训练集。

This document defines the technical implementation of the "Intelligent Training Data Generation Framework for Local Repositories," focusing on how to automatically generate high-quality training sets covering business logic and architecture design with detailed reasoning traces.

## 1. 训练集结构设计 / Training Set Structure

为确保微调后的模型能够理解复杂的业务流程并生成合理的架构设计，我们设计了包含丰富元数据的结构化训练集。

To ensure the fine-tuned model understands complex business processes and generates sound architectural designs, we designed a structured training set with rich metadata.

### 1.1 场景 1：业务流程问答 (Function-level QA)
- **目标**：提取函数逻辑、业务规则及潜在边界。
- **数据组成**：
  - **Instruction**：针对特定函数的分析请求。
  - **Input**：包含完整函数源码、文件路径、Docstring 及启发式复杂度指标。
  - **Output**：
    - `<thought>`：结构化的推理步骤（如：1. 分析输入参数 -> 2. 识别核心业务判断 -> 3. 推导返回值逻辑）。
    - **Answer**：对业务逻辑的准确描述。

### 1.2 场景 2：架构设计方案 (Class-level Design)
- **目标**：基于现有架构骨架（Skeletal Architecture）解决新增需求。
- **数据组成**：
  - **Instruction**：一个具体的业务需求描述。
  - **Input**：目标类的定义、继承链、现有方法签名（不含实现）及类之间的关联元数据。
  - **Output**：
    - `<thought>`：设计推理轨迹（如：1. 评估现有方法复用性 -> 2. 确定新增接口位置 -> 3. 权衡设计模式选择）。
    - **Solution**：具体的架构设计建议或代码实现方案。

## 2. 数据多样性与代表性 / Diversity & Representativeness

系统通过以下策略确保生成的训练集能够代表真实世界的代码复杂性：

1.  **多维度切片**：不局限于单一目录，递归扫描整个仓库并利用 AST 区分简单、中等与复杂代码块。
2.  **复杂度驱动生成**：在 `scenario_processor.py` 中，根据代码复杂度动态调整推理轨迹的深度（3-8 步），确保简单逻辑不啰嗦，复杂逻辑有深度。
3.  **异构仓库采样**：测试阶段使用了三个规模与复杂度差异显著的公开仓库进行验证：
    - **小型 (FastAPI)**：侧重验证 Web 后端的基础 CRUD 业务逻辑提取。
    - **中型 (Saleor)**：侧重验证电商核心流程（如结账、库存）中的复杂业务规则。
    - **异型 (Home Assistant)**：侧重验证在超大规模、高度模块化环境下的架构分析与任务生成。
    - [FastAPI Repo](https://github.com/nsidnev/fastapi-realworld-example-app.git) | [Saleor Repo](https://github.com/saleor/saleor.git) | [Home Assistant Repo](https://github.com/home-assistant/core.git)

## 3. 流水线实现细节 / Pipeline Implementation

### 3.1 静态切片 (Stage 1: `code_slicer.py`)
利用 Python `ast` 模块提取代码元数据。
- **元数据捕获**：包含 `parameters`, `returns`, `decorators`, `docstrings` 以及 `heuristic complexity`。

### 3.2 推理轨迹提取 (Stage 2 & 3)
通过结构化的 JSON Prompt，强制 LLM 在返回结果前执行显式的推理步骤。这些步骤在 Stage 4 中被编译为符合 Qwen 2.5 格式的 `<thought>` 标签。

### 3.3 自动化校验 (Stage 4: `dataset_compiler.py`)
- **解析校验**：自动验证 LLM 返回的 JSON 格式及推理步骤的完整性。
- **指标统计**：实时生成 `Parse Success Rate` 与 `Token Distribution` 报告，便于评估数据质量。

## 4. 评判标准实现对照 / Evaluation Criteria Alignment

| 标准 | 技术实现 |
| :--- | :--- |
| **场景覆盖** | 实现函数级问答与类级设计两条独立链路，完全覆盖目标需求。 |
| **处理有效性** | 全流程自动化（切片 -> Batch 处理 -> 格式转换），包含结构化推理字段。 |
| **系统架构** | 采用四阶段解耦设计，支持替换不同 LLM 后端或新增自定义场景。 |
| **数据清晰度** | 保留各阶段 JSONL 中间产物，确保每一个训练样本都可回溯至原始源码位置。 |

## 5. 目录与分层 / Directory Structure
```text
data/
├── 0.cloned_repo/   # 原始代码 (Input)
├── 1.slices/        # 静态分析产物与元数据
├── 3.batch_input/   # 结构化任务 Prompt 集合
├── 4.batch_output/  # LLM 原始回执（含推理轨迹）
├── 5.final_output/  # 最终编译的微调数据集 (JSONL)
└── 6.fine_tune_qwen/ # 微调产物与验证结果
```

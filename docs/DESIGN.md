# 系统设计文档 (Design Document)

## 1. 设计哲学 / Design Philosophy

本方案的核心设计方法是“基于上下文的推理增强”。我们认为，高质量的代码数据集不应仅仅包含“代码-描述”对，而应包含从代码分析到结论的完整思考链条。
The core design philosophy of this project is "Context-Based Reasoning Enhancement." We believe high-quality code datasets should not just contain "code-description" pairs, but a complete chain of thought from code analysis to conclusion.

## 2. 核心架构与关键代码 / Core Architecture & Key Code

### Stage 1: 结构化切片 (Code Slicing) / Stage 1: Code Slicing
利用 Python `ast` 模块进行静态分析，将庞大的仓库拆解为具有独立语义的切片。
Use the Python `ast` module for static analysis, decomposing large repositories into independent semantic slices.

*   关键代码 / Key Code: `src/pipeline/code_slicer.py` 中的 `SimpleCodeAnalyzer`。
*   复杂度评估 / Complexity Assessment: 采用启发式算法（分支语句计数）来区分简单、中等和复杂函数。
    Uses a heuristic algorithm (branch statement counting) to distinguish simple, medium, and complex functions.
```python
# 复杂度计算示例 / Complexity Calculation Example
def _calculate_complexity(self, node: ast.FunctionDef) -> str:
    score = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
            score += 1
    return "simple" if score <= 3 else "medium" if score <= 7 else "complex"
```

### Stage 2: 场景化 Prompts (Scenario Processing) / Stage 2: Scenario Processing
根据切片类型（函数/类）和复杂度，动态生成不同维度的 Prompt。
Dynamically generate Prompts of different dimensions based on slice type (function/class) and complexity.

*   场景 1 (QA) / Scenario 1: 侧重于函数的具体实现逻辑。 Focuses on specific function implementation logic.
*   场景 2 (Design) / Scenario 2: 提供类架构骨架，要求 LLM 在现有设计模式下完成新需求设计。
    Provides class architecture skeletons, requiring the LLM to design new requirements within existing design patterns.
*   关键代码 / Key Code: `src/pipeline/scenario_processor.py` 中的 `_build_scenario1_prompt`.

### Stage 3: 大规模异步处理 (Batch API) / Stage 3: Batch API Processing
利用 OpenAI Batch API 实现成本降低 50% 且支持超大规模并发的处理。
Leverage OpenAI Batch API for 50% cost reduction and support for ultra-large-scale concurrent processing.

*   关键逻辑 / Key Logic: `BatchSubmitter` 封装了文件上传 (`files.create`)、批处理创建 (`batches.create`) 和状态轮询。
    `BatchSubmitter` encapsulates file upload, batch creation, and status polling.

### Stage 4: 逻辑提取与统计 (Dataset Compilation) / Stage 4: Dataset Compilation
这是流水线的收官阶段，负责从 LLM 的 Raw Response 中提取嵌套的 JSON，并转化为最终的微调格式。
The final stage of the pipeline, responsible for extracting nested JSON from LLM raw responses and converting it into the final fine-tuning format.

*   关键代码 / Key Code: `src/pipeline/dataset_compiler.py` 中的 `_get_parsed_content`.
*   Qwen 格式转化 / Qwen Format Conversion: 将推理步骤包裹在 `<thought>` 标签内。
    Wraps reasoning steps within `<thought>` tags.

## 3. 数据流示例结构 / Data Flow Example Structure

### 1. 原始切片 / Original Slice (Stage 1)
```json
{
  "id": "repo_001_func",
  "type": "function",
  "code_snippet": "def add(a, b): return a + b",
  "complexity": "simple",
  "context": {"docstring": "Add two numbers"}
}
```

### 2. 最终训练样本 / Final Training Sample (Stage 4)
```json
{
  "instruction": "分析以下代码片段...",
  "input": "代码内容:\ndef add(a, b): return a + b",
  "output": "<thought>\nStep 1: 识别函数参数 a 和 b。\nStep 2: 识别返回操作为加法。\nConclusion: 这是一个基础的加法辅助函数。\n</thought>\n\n初级开发者提问：这个函数有什么用？\n资深专家解答：该函数用于计算两个数的和..."
}
```

## 4. 统计指标 / Statistical Metrics

系统通过 `DatasetCompiler` 自动计算 / Automatically calculated via `DatasetCompiler`:
*   Avg Reasoning Steps: `total_steps / successful_items`，反映数据集的逻辑深度。 Reflects the logical depth of the dataset.
*   Parse Success Rate: 衡量 LLM 遵循 JSON 输出格式的质量。 Measures the quality of LLM adherence to JSON output format.

## 5. 目录与分层 / Directory & Layering
```text
data/
├── 0.cloned_repo/   # 原始代码 (Input) / Original Code
├── 1.slices/        # 静态分析产物 / Static Analysis Artifacts
├── 3.batch_input/   # LLM 任务清单 / LLM Task List
├── 4.batch_output/  # LLM 原始回执 (Async) / Raw LLM Responses
└── 5.final_output/  # 最终训练数据集 (Output) / Final Training Dataset
```

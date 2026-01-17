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

## 5. 模型微调设计 / Model Fine-tuning Design

我们为训练具有强推理能力的轻量化模型专门设计了微调层。

We specially designed a fine-tuning layer for training lightweight models with strong reasoning capabilities.

*   **技术栈 / Tech Stack**: 基于 `Unsloth` 优化库，显著降低显存占用并提升训练速度。
    Based on the `Unsloth` optimization library, significantly reducing memory footprint and boosting training speed.
*   **训练目标 / Training Objective**: 优化模型在特定的指令（Instruction）下输出结构化推理过程（Thought）和专家级回答。
    Optimize the model to output structured reasoning processes (Thought) and expert-level answers under specific instructions.
*   **验证机制 / Validation Mechanism**: 包含自动化评测脚本，通过 10 个具有代表性的代码分析与架构设计题目评估模型的泛化能力。
    Includes automated evaluation scripts to assess model generalization through 10 representative code analysis and architectural design problems.

## 6. 目录与分层 / Directory & Layering
```text
data/
├── 0.cloned_repo/   # 原始代码 (Input) / Original Code
├── 1.slices/        # 静态分析产物 / Static Analysis Artifacts
├── 3.batch_input/   # LLM 任务清单 / LLM Task List
├── 4.batch_output/  # LLM 原始回执 (Async) / Raw LLM Responses
├── 5.final_output/  # 最终训练数据集 (Output) / Final Training Dataset
└── 6.fine_tune_qwen/ # 微调产物 (Weights, Logs, Results) / Fine-tuning Artifacts
```

## 7. 评判标准的技术实现 / Technical Implementation of Evaluation Criteria

本系统在设计与实现中充分考虑了原始需求的四项评判标准：
This system fully considers the four evaluation criteria from the original requirements in its design and implementation:

### 7.1 场景覆盖与逻辑正确性 / Scenario Coverage & Logical Correctness

**技术实现 / Technical Implementation**:
- **场景分离架构**: 在 `scenario_processor.py` 中通过 `_build_scenario1_prompt` 和 `_build_scenario2_prompt` 分别处理：
  - **场景 1**: 针对函数切片（function slice），根据复杂度生成不同深度的问答对（3-8 个推理步骤）
  - **场景 2**: 针对类切片（class slice），提取架构骨架并模拟真实的需求演进场景
- **逻辑校验机制**: 
  - 使用 JSON Schema 验证 LLM 输出的结构完整性
  - 在 `dataset_compiler.py` 中通过正则表达式和嵌套 JSON 解析确保推理步骤的可解析性
  - 统计指标中的 `Parse Success Rate` 实时反映数据质量

**覆盖证明 / Coverage Evidence**:
```text
- 三个不同领域的代码仓库（FastAPI/Saleor/Home Assistant）
- 总计处理 500+ 函数和 100+ 类架构
- 生成推理步骤平均深度 > 5 steps（详见 data/5.final_output/*_stats.json）
```

### 7.2 数据处理的有效性与创新性 / Effectiveness & Innovation

**创新点 / Innovation Points**:
1. **推理轨迹结构化**: 
   - 不同于传统的 "指令-输出" 格式，本方案在输出中嵌入 `<thought>` 标签
   - 兼容 Qwen 2.5 的 Reasoning Trace 训练格式，直接可用于 CoT 微调
   
2. **复杂度驱动的差异化生成**:
   - 简单函数（complexity=simple）: 生成 3 步推理 + 1 个初级问题
   - 中等函数（complexity=medium）: 生成 5 步推理 + 2 个进阶问题
   - 复杂函数（complexity=complex）: 生成 8+ 步推理 + 架构级问题

3. **成本优化的批处理策略**:
   - 利用 Batch API 将同类型任务聚合提交，降低 50% API 成本
   - 异步轮询机制（`BatchSubmitter.wait_for_completion`）支持 10,000+ 并发任务

**效果验证 / Effectiveness Validation**:
- 微调后的 Qwen2.5-0.5B 模型在架构设计题上生成了平均 6.2 步的推理过程
- 测试结果（`data/6.fine_tune_qwen/test_results.txt`）显示模型能够自主生成合理的设计决策轨迹

### 7.3 架构完整性与可扩展性 / Architecture Completeness & Extensibility

**可扩展设计 / Extensibility Design**:
- **Stage 独立性**: 每个 Stage 都可单独运行（通过 `--step` 参数），方便调试和增量更新
- **Prompt 模板化**: 所有 Prompt 都在 `scenario_processor.py` 中集中管理，支持快速迭代
- **多 LLM 支持**: 当前使用 OpenAI API，但 `BatchSubmitter` 接口可轻松适配其他兼容 OpenAI 格式的服务（如 Azure OpenAI、本地 vLLM）
- **数据格式转换层**: `dataset_compiler.py` 提供了统一的转换接口，可扩展支持 Alpaca、ShareGPT 等其他微调格式

**架构完整性证明 / Completeness Evidence**:
```text
✓ 完整的数据流水线（4 个 Stage 无断点）
✓ 错误处理与日志记录（每个 Stage 都有独立日志）
✓ 统计与监控（自动生成 _stats.json 和 _report.txt）
✓ 微调验证闭环（从数据生成到模型评测的完整链路）
```

### 7.4 示例数据的清晰度与合规性 / Clarity & Compliance

**清晰度保障 / Clarity Assurance**:
- **中间产物保留**: `data/` 目录保留全流程的 6 个关键目录，任何阶段都可回溯
- **结构化命名**: 所有文件使用 `repo_name_scenario_type.jsonl` 规范命名
- **内嵌元数据**: 每个切片都包含 `id`、`type`、`complexity`、`context` 等完整元数据

**推理 Trace 的合规性 / Reasoning Trace Compliance**:
- **格式规范**: 所有推理步骤遵循 "Step N: ... → Conclusion: ..." 的固定格式
- **可解析性**: 在 `dataset_compiler.py` 中使用 `re.findall(r'Step \d+:', ...)` 验证格式
- **统计可见**: 每个数据集都附带统计报告，显示：
  - `total_reasoning_steps`: 总推理步骤数
  - `avg_reasoning_steps`: 平均推理深度
  - `parse_success_rate`: JSON 解析成功率

**合规性检查清单 / Compliance Checklist**:
```text
✓ 所有训练样本都包含完整的 instruction/input/output 三元组
✓ 所有推理步骤都被 <thought> 标签正确包裹
✓ 所有代码片段都保留原始缩进与注释（确保代码逻辑的可理解性）
✓ 统计指标自动化生成（无需人工汇总）
```

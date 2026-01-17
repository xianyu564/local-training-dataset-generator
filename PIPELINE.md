# Pipeline Workflow Guide
# 流水线工作流指南

This guide explains the multi-stage pipeline for generating training datasets from code repositories.
本指南说明了从代码仓库生成训练数据集的多阶段流水线。

## Pipeline Overview / 流水线概览

The pipeline consists of 5 stages with manual review checkpoints:
流水线包含5个阶段和人工审核检查点：

```
[Stage 1] Code Slicing → [Checkpoint 1] Manual Review
    ↓
[Stage 3] Batch Processing Preparation → Submit to GPT Batch API
    ↓
[Checkpoint 2] Manual Review of Generated Data
    ↓
[Stage 5] Dataset Compilation → Statistics & Shuffle → Final JSONL
```

## Stage Details / 阶段详情

### Stage 1: Code Slicing / 代码切片

**Purpose**: Extract code segments from repositories for analysis
**目的**：从仓库中提取代码片段进行分析

**Input**: 
- GitHub repository URLs
- Configuration settings

**Output**:
- `slices/code_slices_TIMESTAMP.jsonl` - All extracted code slices

**Process**:
```python
from src.pipeline.code_slicer import CodeSlicer

slicer = CodeSlicer(output_dir="slices")
slices = slicer.slice_repository(
    repo_path="/path/to/repo",
    repo_name="owner/repo",
    max_files=50
)
slices_file = slicer.export_slices()
```

**What to Review**:
- Check if slices are meaningful code segments
- Verify complexity classifications
- Filter out test files or generated code
- Ensure diversity across modules

### Checkpoint 1: Manual Review / 人工审核检查点1

**Purpose**: Human review and filtering of code slices
**目的**：人工审核和过滤代码切片

**Process**:
1. Review `slices/code_slices_TIMESTAMP.jsonl`
2. Identify slices suitable for training data
3. Remove irrelevant, duplicate, or low-quality slices
4. Save approved slices to `reviewed_slices/` directory

**Tips**:
- Look for slices with clear business logic
- Prefer functions with docstrings
- Include diverse complexity levels
- Separate slices for Scenario 1 vs Scenario 2

### Stage 3: Batch Processing Preparation / 批处理准备

**Purpose**: Prepare prompts for GPT Batch API
**目的**：为GPT批处理API准备提示

**Input**:
- `reviewed_slices/*.jsonl` - Manually approved slices
- `llm_config.yaml` - LLM configuration (gitignored)

**Output**:
- `batch_input/scenario1_batch_input_TIMESTAMP.jsonl` - Q&A prompts
- `batch_input/scenario2_batch_input_TIMESTAMP.jsonl` - Design prompts

**Process**:
```python
from src.pipeline.batch_processor import BatchProcessor

processor = BatchProcessor(
    config_path="llm_config.yaml",
    output_dir="batch_input"
)

# Create Scenario 1 requests (Q&A)
scenario1_requests = processor.create_scenario1_prompts(function_slices)
scenario1_file = processor.export_batch_requests(scenario1_requests, "scenario1")

# Create Scenario 2 requests (Design)
scenario2_requests = processor.create_scenario2_prompts(class_slices)
scenario2_file = processor.export_batch_requests(scenario2_requests, "scenario2")
```

**Submitting to OpenAI Batch API**:
```bash
# Upload batch file
curl https://api.openai.com/v1/files \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F purpose="batch" \
  -F file="@batch_input/scenario1_batch_input.jsonl"

# Create batch job
curl https://api.openai.com/v1/batches \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input_file_id": "file-abc123",
    "endpoint": "/v1/chat/completions",
    "completion_window": "24h"
  }'

# Check status
curl https://api.openai.com/v1/batches/$BATCH_ID \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Download results when complete
curl https://api.openai.com/v1/files/$OUTPUT_FILE_ID/content \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  > batch_output/scenario1_responses.jsonl
```

### Checkpoint 2: Manual Review of Generated Data / 生成数据的人工审核

**Purpose**: Review LLM-generated Q&A pairs and design solutions
**目的**：审核LLM生成的问答对和设计方案

**Process**:
1. Review `batch_output/scenario1_responses.jsonl`
2. Review `batch_output/scenario2_responses.jsonl`
3. Check quality of:
   - Question relevance and clarity
   - Answer accuracy and completeness
   - Reasoning trace logic
   - Design solution feasibility
4. Filter out low-quality items
5. Save approved items back to batch_output/

**Quality Criteria**:
- ✅ Clear and specific questions
- ✅ Accurate and detailed answers
- ✅ Logical reasoning traces
- ✅ Relevant code references
- ❌ Generic or vague responses
- ❌ Incorrect technical information
- ❌ Missing reasoning steps

### Stage 5: Dataset Compilation / 数据集编译

**Purpose**: Compile final training dataset with statistics
**目的**：编译最终训练数据集并生成统计信息

**Input**:
- `batch_output/scenario1_responses.jsonl` - Approved Scenario 1 data
- `batch_output/scenario2_responses.jsonl` - Approved Scenario 2 data

**Output**:
- `final_output/training_dataset_TIMESTAMP.jsonl` - Final shuffled dataset
- `final_output/dataset_statistics_TIMESTAMP.json` - Statistics
- `final_output/review_summary_TIMESTAMP.md` - Human-readable summary

**Process**:
```python
from src.pipeline.dataset_compiler import DatasetCompiler

compiler = DatasetCompiler(output_dir="final_output")

# Load approved data
compiler.load_scenario_data(
    scenario1_file="batch_output/scenario1_responses.jsonl",
    scenario2_file="batch_output/scenario2_responses.jsonl"
)

# Generate statistics
stats_file = compiler.export_statistics()

# Export final training dataset (shuffled)
training_file = compiler.export_training_dataset(shuffle=True, seed=42)

# Create review summary
summary_file = compiler.create_review_summary()
```

**Statistics Include**:
- Total count by scenario
- Distribution by complexity, repository, architecture style
- Average reasoning steps and decision points
- Percentage split between scenarios

## Complete Example / 完整示例

See `examples/pipeline_workflow.py` for a complete end-to-end example:

```bash
python examples/pipeline_workflow.py
```

## Configuration / 配置

### LLM Configuration (llm_config.yaml)

**IMPORTANT**: This file is gitignored. Copy from template:
**重要**：此文件已被gitignore。从模板复制：

```bash
cp llm_config.yaml.template llm_config.yaml
# Edit llm_config.yaml with your API key
```

Example configuration:
```yaml
api_key: "sk-..."
model: "gpt-4o-mini"
max_tokens: 2000
temperature: 0.7
batch:
  completion_window: "24h"
  description: "Training dataset generation"
```

### Repositories Configuration

The pipeline supports multiple repositories. Recommended repositories:
流水线支持多个仓库。推荐的仓库：

1. **fastapi-realworld-example-app** - FastAPI backend with clear business logic
2. **flask** - Popular web framework with extensive codebase
3. **requests** - HTTP library with clean API design

## Directory Structure / 目录结构

```
.
├── slices/                    # Stage 1 output
│   └── code_slices_*.jsonl
├── reviewed_slices/           # Checkpoint 1 output
│   └── approved_slices.jsonl
├── batch_input/               # Stage 3 output
│   ├── scenario1_batch_input_*.jsonl
│   └── scenario2_batch_input_*.jsonl
├── batch_output/              # GPT Batch API results
│   ├── scenario1_responses.jsonl
│   └── scenario2_responses.jsonl
├── final_output/              # Stage 5 output
│   ├── training_dataset_*.jsonl
│   ├── dataset_statistics_*.json
│   └── review_summary_*.md
└── llm_config.yaml           # LLM configuration (gitignored)
```

## Data Formats / 数据格式

### Code Slice Format (Stage 1)

```json
{
  "id": "repo_00001_func",
  "type": "function",
  "repository": "owner/repo",
  "file_path": "src/module/file.py",
  "name": "function_name",
  "start_line": 10,
  "end_line": 25,
  "code_snippet": "def function_name():\n    ...",
  "complexity": "medium",
  "context": {
    "docstring": "Function docstring",
    "parameters": ["param1", "param2"],
    "returns": "str"
  }
}
```

### Batch Request Format (Stage 3)

```json
{
  "custom_id": "scenario1_repo_00001_func",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": {
    "model": "gpt-4o-mini",
    "messages": [...],
    "max_tokens": 2000
  }
}
```

### Training Data Format (Stage 5)

**Scenario 1 (Q&A)**:
```json
{
  "training_scenario": "scenario1_qa",
  "question": "How does this function handle errors?",
  "answer": "The function uses try-except blocks...",
  "reasoning_trace": {
    "steps": [
      {
        "step_number": 1,
        "description": "Identify error handling pattern",
        "code_reference": "try-except block",
        "reasoning": "Standard Python exception handling"
      }
    ],
    "conclusion": "Robust error handling implemented"
  },
  "business_rules": ["Must handle network timeouts"]
}
```

**Scenario 2 (Design)**:
```json
{
  "training_scenario": "scenario2_design",
  "requirement": {
    "title": "User authentication system",
    "description": "Implement secure login..."
  },
  "design_solution": {
    "overview": "JWT-based authentication with refresh tokens",
    "architecture": {...}
  },
  "reasoning_trace": {
    "decision_points": [...]
  }
}
```

## Best Practices / 最佳实践

### 1. Repository Selection / 仓库选择
- Choose repositories with clear business logic
- Prefer well-documented code
- Include diverse domains (web, data, API, etc.)

### 2. Manual Review / 人工审核
- Review at least 10% of samples from each stage
- Look for patterns in quality issues
- Maintain review notes for improvement

### 3. Batch Processing / 批处理
- Use gpt-4o-mini for cost efficiency
- Process in batches of 100-500 items
- Monitor token usage and costs

### 4. Quality Control / 质量控制
- Set minimum quality thresholds
- Remove duplicate or similar items
- Ensure balanced distribution across scenarios

## Troubleshooting / 故障排除

### Issue: No slices generated
**Solution**: Check if repository contains Python files, adjust max_files parameter

### Issue: Batch API errors
**Solution**: Verify API key, check request format, review OpenAI API status

### Issue: Low-quality generated data
**Solution**: Improve prompts in batch_processor.py, add more context, use better examples

### Issue: Imbalanced scenario distribution
**Solution**: Adjust filtering criteria, generate more slices for underrepresented scenario

## Next Steps / 下一步

After generating your training dataset:

1. **Validate Quality**: Review statistics and samples
2. **Fine-tune Model**: Use the JSONL file for model training
3. **Iterate**: Refine prompts and regenerate if needed
4. **Monitor**: Track model performance with your dataset

---

**Need Help?** / **需要帮助？**
- Check examples in `examples/` directory
- Review source code in `src/pipeline/`
- Open an issue on GitHub

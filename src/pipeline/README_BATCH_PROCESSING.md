# Batch Processing Guide
# 批处理指南

This guide explains how to use the split batch processing system.
本指南说明如何使用拆分的批处理系统。

## Overview / 概述

The batch processing has been split into two components:
批处理已拆分为两个组件：

1. **Scenario Processor** (`scenario_processor.py`): Converts reviewed slices to batch input
   **场景处理器**：将审核后的切片转换为批处理输入

2. **Batch Submitter** (`batch_submitter.py`): Submits batch input to OpenAI API
   **批处理提交器**：将批处理输入提交到OpenAI API

## Directory Structure / 目录结构

```
data/
├── 2.reviewed_slices/     # Input: Manually reviewed slice files
│   └── *.jsonl            # Reviewed slice JSONL files
├── 3.batch_input/         # Output: Batch API input files
│   ├── scenario1_batch_input_*.jsonl
│   └── scenario2_batch_input_*.jsonl
├── 4.batch_output/        # Output: Batch job info and results
│   ├── batch_job_*.json
│   ├── batch_results_*.jsonl
│   └── batch_submission_results_*.json
```

## Step 1: Process Reviewed Slices / 步骤1：处理审核后的切片

Convert `data/2.reviewed_slices` to `data/3.batch_input`:
将 `data/2.reviewed_slices` 转换为 `data/3.batch_input`：

```bash
# Default settings
python src/pipeline/scenario_processor.py

# Custom settings
python src/pipeline/scenario_processor.py \
  --reviewed-dir data/2.reviewed_slices \
  --output-dir data/3.batch_input \
  --max-scenario1 100 \
  --max-scenario2 50
```

**What it does / 功能说明**:
- Reads all JSONL files from `data/2.reviewed_slices`
- Splits slices by type (function → scenario1, class → scenario2)
- Creates OpenAI batch API request format
- Saves to `data/3.batch_input/`

## Step 2: Submit to OpenAI / 步骤2：提交到OpenAI

Submit `data/3.batch_input` files to OpenAI Batch API:
将 `data/3.batch_input` 文件提交到OpenAI批处理API：

### Prerequisites / 前置条件

1. **Install OpenAI package / 安装OpenAI包**:
   ```bash
   pip install openai
   ```

2. **Create config.json / 创建配置文件**:
   ```json
   {
     "api_key": "your-openai-api-key-here"
   }
   ```

### Submit batches / 提交批处理

```bash
# Submit all batch files
python src/pipeline/batch_submitter.py --config config.json

# Custom directories
python src/pipeline/batch_submitter.py \
  --config config.json \
  --input-dir data/3.batch_input \
  --output-dir data/4.batch_output
```

**What it does / 功能说明**:
- Reads your OpenAI API key from `config.json`
- Uploads each batch input file to OpenAI
- Creates batch jobs with 24h completion window
- Saves job information to `data/4.batch_output/`

## Step 3: Monitor and Download / 步骤3：监控和下载

### Check batch status / 检查批处理状态

```bash
# List all active batches
python src/pipeline/batch_submitter.py --config config.json --list-active

# Check specific batch status
python src/pipeline/batch_submitter.py --config config.json --check-status batch_abc123
```

### Download completed results / 下载完成的结果

```bash
# Download results for a specific batch
python src/pipeline/batch_submitter.py --config config.json --download-results batch_abc123
```

**Output files / 输出文件**:
- `batch_results_{batch_id}.jsonl`: The actual LLM responses
- Job status information saved to batch job files

## Configuration / 配置

### config.json format / config.json 格式

```json
{
  "api_key": "sk-your-openai-api-key-here"
}
```

### Default directories / 默认目录

- Input reviewed slices: `data/2.reviewed_slices`
- Output batch input: `data/3.batch_input`
- Output batch results: `data/4.batch_output`

## Error Handling / 错误处理

### Common issues / 常见问题

1. **Missing config.json**: Make sure the file exists with valid API key
2. **OpenAI package not installed**: Run `pip install openai`
3. **No reviewed slices**: Check that `data/2.reviewed_slices` contains JSONL files
4. **API quota exceeded**: Monitor your OpenAI usage dashboard

### Batch job failures / 批处理作业失败

- Failed submissions are logged in `batch_submission_results_*.json`
- Individual batch errors can be checked with `--check-status`
- Failed batches may need to be resubmitted

## Next Steps / 后续步骤

After downloading batch results, proceed to **Dataset Compilation**:
下载批处理结果后，继续进行**数据集编译**：

```bash
# Use dataset_compiler.py to combine results into final training dataset
python src/pipeline/dataset_compiler.py
```

## Cost Estimation / 成本估算

- GPT-4o-mini: ~$0.0015 per 1K tokens
- Typical scenario1 request: ~500 tokens → ~$0.00075
- Typical scenario2 request: ~800 tokens → ~$0.0012
- Batch of 100 scenario1 + 50 scenario2: ~$0.15 (before discounts)
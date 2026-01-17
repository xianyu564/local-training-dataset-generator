# 使用手册 / Usage Guide

本文档说明如何运行自动化流水线，从本地仓库生成包含推理轨迹的智能训练数据集。

This guide explains how to run the automated pipeline to generate intelligent training datasets with reasoning traces from local repositories.

## 1. 环境准备 / Preparation

```bash
# 安装核心依赖 / Install dependencies
pip install -r requirements.txt

# 配置 API 密钥 / Configure API Key
# 编辑或创建 config.json
{
  "openai": {
    "api_key": "sk-...",
    "model": "gpt-5-nano-2025-08-07"
  }
}
```

## 2. 运行流水线 / Running the Pipeline

流水线分为四个标准阶段，需按顺序执行：

### Stage 1: 代码静态切片 / Static Slicing
解析源码并提取元数据。
```bash
python src/pipeline/code_slicer.py data/0.cloned_repo/my_project/ --repo-name my_project
```

### Stage 2: 任务场景生成 / Task Generation
构建针对 QA 和设计方案的 Prompt。
```bash
python src/pipeline/scenario_processor.py --reviewed-dir data/1.slices/my_project/ --output-dir data/3.batch_input/my_project/
```

### Stage 3: 批处理提交与下载 / Batch Processing
利用 OpenAI Batch API 高效获取 LLM 回复。
```bash
# 提交任务 / Submit
python src/pipeline/batch_submitter.py --input-dir data/3.batch_input/your_project/ --output-dir data/4.batch_output/your_project/

# 下载结果 (待状态为 completed 后) / Download results
python src/pipeline/batch_submitter.py --download-results <batch_id> --output-dir data/4.batch_output/your_project/
```
*注意：下载后请将 `batch_results_*.jsonl` 按场景重命名为 `scenario1_output.jsonl` 或 `scenario2_output.jsonl`。*

### Stage 4: 数据集编译 / Compilation
将回执转换为最终的微调 JSONL 格式。
```bash
python src/pipeline/dataset_compiler.py --batch-output-dir data/4.batch_output/ --output-dir data/5.final_output/ --source-data-dir data/1.slices/
```

## 3. 验证与微调 / Validation & Fine-tuning

生成的训练集位于 `data/5.final_output/`。如需进行模型微调验证：
1.  参考 `docs/FINETUNE.md` 安装微调相关依赖。
2.  运行 `src/fine-tune/train.py` 开始微调。
3.  使用 `src/fine-tune/run_inference.py` 评估生成效果。

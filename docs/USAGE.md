# 使用手册 (Usage Guide)

本文档介绍如何手动运行本项目流水线的各个阶段。
This document describes how to manually run the various stages of this project's pipeline.

## 1. 准备阶段 / Preparation

1.  **安装依赖 / Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **配置 API / Configure API**:
    创建 `config.json`，填入你的 OpenAI API Key:
    Create `config.json` and enter your OpenAI API Key:
    ```json
    {
      "openai": {
        "api_key": "sk-...",
        "model": "gpt-5-nano-2025-08-07"
      }
    }
    ```
3.  **准备源码 / Prepare Source Code**:
    将待处理的代码仓库文件夹放入 `data/0.cloned_repo/`。例如：`data/0.cloned_repo/my_project/`。
    Place the target repository folder into `data/0.cloned_repo/`. For example: `data/0.cloned_repo/my_project/`.

## 2. 运行流水线 / Running the Pipeline

### 阶段 1: 代码切片 (Code Slicing) / Stage 1: Code Slicing
将 Python 源码解析为结构化的函数和类切片。
Parse Python source code into structured function and class slices.
```bash
python src/pipeline/code_slicer.py data/0.cloned_repo/my_project/ --repo-name my_project
```
*   **输入 / Input**: `data/0.cloned_repo/my_project/`
*   **输出 / Output**: `data/1.slices/my_project/code_slices.jsonl`

### 阶段 2: 场景处理 (Scenario Processing) / Stage 2: Scenario Processing
将切片转化为 LLM 任务。
Transform slices into LLM tasks.
```bash
python src/pipeline/scenario_processor.py --reviewed-dir data/1.slices/my_project/ --output-dir data/3.batch_input/my_project/
```
*   **输入 / Input**: `data/1.slices/my_project/`
*   **输出 / Output**: `data/3.batch_input/my_project/scenario1_batch_input_*.jsonl` 等。

### 阶段 3: 批处理提交与下载 (Batch API) / Stage 3: Batch Submission & Download
#### 提交任务 / Submit Task:
```bash
python src/pipeline/batch_submitter.py --input-dir data/3.batch_input/my_project/ --output-dir data/4.batch_output/my_project/
```
*注意：提交后需等待 OpenAI 处理（通常几小时）。*
*Note: After submission, wait for OpenAI processing (typically a few hours).*

#### 检查状态与下载 / Check Status & Download:
```bash
# 列出活跃任务 / List active jobs
python src/pipeline/batch_submitter.py --list-active

# 下载结果 / Download results (替换 <batch_id> / replace <batch_id>)
python src/pipeline/batch_submitter.py --download-results <batch_id> --output-dir data/4.batch_output/my_project/
```
*下载的文件应命名为 `scenario1_output.jsonl` 等，放在对应的仓库目录下。*
*Downloaded files should be named `scenario1_output.jsonl`, etc., and placed in the corresponding repository directory.*

### 阶段 4: 数据集编译 (Dataset Compilation) / Stage 4: Dataset Compilation
将 LLM 返回的结果合并并转化为训练格式。
Merge LLM responses and transform them into the training format.
```bash
python src/pipeline/dataset_compiler.py --batch-output-dir data/4.batch_output/ --output-dir data/5.final_output/ --source-data-dir data/1.slices/
```
*   **输入 / Input**: `data/4.batch_output/` 和 `data/1.slices/` (用于代码映射 / for code mapping)
*   **输出 / Output**: `data/5.final_output/` 下的 `train_dataset_*.jsonl` 和 `dataset_statistics_*.json`。

## 3. 模型微调 / Model Fine-tuning

微调流程专门设计用于在本地或远程服务器上训练模型。

The fine-tuning workflow is specifically designed for training models locally or on remote servers.

1.  **准备环境 / Environment**:
    ```bash
    pip install -r src/fine-tune/requirements.txt
    ```

2.  **启动训练 (Local) / Start Training**:
    ```bash
    python src/fine-tune/train.py
    ```
    该脚本会自动搜索 `data/5.final_output/` 下的最新数据集并开始训练。
    The script will automatically search for the latest dataset in `data/5.final_output/` and begin training.

3.  **运行 UI (Gradio) / Run UI**:
    ```bash
    python src/fine-tune/app.py
    ```
    启动后可进行交互式聊天、测试或发起远程 Space 训练任务。
    Launch for interactive chat, testing, or triggering remote Space training tasks.

## 4. 目录结构总结 / Directory Structure Summary

| 目录 / Directory | 阶段 / Stage | 说明 / Description |
| :--- | :--- | :--- |
| `data/0.cloned_repo/` | 输入 / Input | 原始代码仓库 / Original repositories |
| `data/1.slices/` | Stage 1 | 结构化代码片段 / Structured code slices |
| `data/3.batch_input/` | Stage 2 | 发往 OpenAI 的 JSONL 请求 / JSONL requests for OpenAI |
| `data/4.batch_output/` | Stage 3 | OpenAI 返回的原始结果 / Raw responses from OpenAI |
| `data/5.final_output/` | Stage 4 | 最终生成的微调数据集 / Final fine-tuning dataset |

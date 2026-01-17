# Quick Reference Guide
# 快速参考指南

This is a quick reference for using the training dataset generation pipeline.
这是使用训练数据集生成流水线的快速参考。

## Setup / 设置

```bash
# 1. Clone the repository
git clone https://github.com/xianyu564/local-training-dataset-generator.git
cd local-training-dataset-generator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure LLM (copy template and edit)
cp llm_config.yaml.template llm_config.yaml
# Edit llm_config.yaml with your OpenAI API key
```

## Stage 1: Code Slicing / 代码切片

```python
from src.pipeline.code_slicer import CodeSlicer
from src.analyzers.code_analyzer import RepositoryCloner

# Clone repository (if needed)
repo_path = RepositoryCloner.clone(
    "https://github.com/nsidnev/fastapi-realworld-example-app.git",
    "/tmp/datasets/fastapi-realworld"
)

# Slice the repository
slicer = CodeSlicer(output_dir="slices")
slices = slicer.slice_repository(
    repo_path=repo_path,
    repo_name="nsidnev/fastapi-realworld-example-app",
    max_files=50
)

# Export to JSONL
slices_file = slicer.export_slices()
print(f"Slices saved to: {slices_file}")

# View statistics
stats = slicer.get_statistics()
print(f"Total slices: {stats['total_slices']}")
print(f"By complexity: {stats['by_complexity']}")
```

**Output**: `slices/code_slices_TIMESTAMP.jsonl`

## Checkpoint 1: Manual Review / 人工审核

```bash
# Review the slices file
cat slices/code_slices_*.jsonl | jq .

# Filter and save approved slices
mkdir -p reviewed_slices
# Manually copy approved slices to reviewed_slices/
```

## Stage 3: Batch Processing / 批处理

```python
from src.pipeline.batch_processor import BatchProcessor
import json

# Load reviewed slices
with open('reviewed_slices/approved_slices.jsonl') as f:
    slices = [json.loads(line) for line in f if line.strip()]

# Initialize processor
processor = BatchProcessor(
    config_path="llm_config.yaml",
    output_dir="batch_input"
)

# Separate slices by scenario
scenario1_slices = [s for s in slices if s['type'] == 'function'][:20]
scenario2_slices = [s for s in slices if s['type'] == 'class'][:10]

# Create batch requests for Scenario 1 (Q&A)
requests = processor.create_scenario1_prompts(scenario1_slices)
batch_file_1 = processor.export_batch_requests(requests, "scenario1")

# Create batch requests for Scenario 2 (Design)
requests = processor.create_scenario2_prompts(scenario2_slices)
batch_file_2 = processor.export_batch_requests(requests, "scenario2")

print(f"Batch files ready:")
print(f"  Scenario 1: {batch_file_1}")
print(f"  Scenario 2: {batch_file_2}")
```

**Submit to OpenAI**:
```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Upload and create batch job (example for scenario1)
# 1. Upload file
FILE_ID=$(curl -s https://api.openai.com/v1/files \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F purpose="batch" \
  -F file="@batch_input/scenario1_batch_input.jsonl" | jq -r .id)

# 2. Create batch
BATCH_ID=$(curl -s https://api.openai.com/v1/batches \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"input_file_id\": \"$FILE_ID\",
    \"endpoint\": \"/v1/chat/completions\",
    \"completion_window\": \"24h\"
  }" | jq -r .id)

echo "Batch ID: $BATCH_ID"

# 3. Check status (repeat until completed)
curl https://api.openai.com/v1/batches/$BATCH_ID \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 4. Download results when completed
OUTPUT_FILE_ID=$(curl -s https://api.openai.com/v1/batches/$BATCH_ID \
  -H "Authorization: Bearer $OPENAI_API_KEY" | jq -r .output_file_id)

curl https://api.openai.com/v1/files/$OUTPUT_FILE_ID/content \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  > batch_output/scenario1_responses.jsonl
```

## Checkpoint 2: Review Generated Data / 审核生成数据

```bash
# Review batch outputs
cat batch_output/scenario1_responses.jsonl | jq .
cat batch_output/scenario2_responses.jsonl | jq .

# Filter low-quality items manually
# Keep approved items in batch_output/
```

## Stage 5: Final Compilation / 最终编译

```python
from src.pipeline.dataset_compiler import DatasetCompiler

# Initialize compiler
compiler = DatasetCompiler(output_dir="final_output")

# Load approved data
compiler.load_scenario_data(
    scenario1_file="batch_output/scenario1_responses.jsonl",
    scenario2_file="batch_output/scenario2_responses.jsonl"
)

# Export final training dataset
training_file = compiler.export_training_dataset(shuffle=True, seed=42)
print(f"Training dataset: {training_file}")

# Export statistics
stats_file = compiler.export_statistics()
print(f"Statistics: {stats_file}")

# Create review summary
summary_file = compiler.create_review_summary()
print(f"Review summary: {summary_file}")
```

**Output Files**:
- `final_output/training_dataset_TIMESTAMP.jsonl` - Ready for fine-tuning
- `final_output/dataset_statistics_TIMESTAMP.json` - Statistics
- `final_output/review_summary_TIMESTAMP.md` - Human-readable summary

## Common Commands / 常用命令

```bash
# View statistics
python -c "
from src.pipeline.dataset_compiler import DatasetCompiler
import json
compiler = DatasetCompiler()
compiler.load_scenario_data('batch_output/scenario1_responses.jsonl', 'batch_output/scenario2_responses.jsonl')
print(json.dumps(compiler.generate_statistics(), indent=2))
"

# Count items
wc -l final_output/training_dataset_*.jsonl

# View random sample
shuf -n 5 final_output/training_dataset_*.jsonl | jq .

# Split dataset
head -n 80 final_output/training_dataset.jsonl > train.jsonl
tail -n 20 final_output/training_dataset.jsonl > test.jsonl
```

## Recommended Repositories / 推荐的仓库

1. **fastapi-realworld-example-app**
   ```python
   repo_url = "https://github.com/nsidnev/fastapi-realworld-example-app.git"
   ```

2. **flask**
   ```python
   repo_url = "https://github.com/pallets/flask.git"
   ```

3. **requests**
   ```python
   repo_url = "https://github.com/psf/requests.git"
   ```

## Tips / 提示

- **Start Small**: Begin with 10-20 slices per scenario to test the pipeline
- **Review Often**: Check quality at each checkpoint
- **Cost Control**: Use gpt-4o-mini for batch processing to save costs
- **Diversity**: Include different code complexities and patterns
- **Iteration**: Refine prompts based on output quality

## Troubleshooting / 故障排除

**Issue**: Import errors
```bash
pip install -r requirements.txt
```

**Issue**: Batch API timeouts
```bash
# Check batch status regularly
curl https://api.openai.com/v1/batches/$BATCH_ID -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Issue**: Low quality outputs
- Review and improve prompts in `src/pipeline/batch_processor.py`
- Add more context to code slices
- Filter slices more carefully in Checkpoint 1

---

For more details, see [PIPELINE.md](PIPELINE.md)

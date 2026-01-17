"""
Config-Driven Pipeline Workflow
使用配置驱动的流水线工作流

This script demonstrates using config.yaml to drive the pipeline process.
此脚本演示使用config.yaml驱动流水线过程。
"""

import logging
from pathlib import Path

from src.pipeline.code_slicer import CodeSlicer
from src.pipeline.batch_processor import BatchProcessor
from src.pipeline.dataset_compiler import DatasetCompiler
from src.analyzers.code_analyzer import RepositoryCloner
from src.utils.config_loader import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main pipeline workflow using configuration"""
    
    # Load configuration
    config = get_config("config.yaml")
    
    print("=" * 60)
    print("Config-Driven Training Dataset Generation Pipeline")
    print("配置驱动的训练数据集生成流水线")
    print("=" * 60)
    
    # Get pipeline settings
    pipeline_config = config.pipeline
    repo_config = config.repository
    
    slices_dir = pipeline_config.get('slices_dir', 'slices')
    batch_input_dir = pipeline_config.get('batch_input_dir', 'batch_input')
    final_output_dir = pipeline_config.get('final_output_dir', 'final_output')
    
    # ========================================================================
    # STAGE 1: Code Slicing from configured repositories
    # 阶段1：从配置的仓库进行代码切片
    # ========================================================================
    print("\n[STAGE 1] Code Slicing / 代码切片")
    print("-" * 60)
    
    slicer = CodeSlicer(output_dir=slices_dir)
    repositories = pipeline_config.get('repositories', [])
    
    if not repositories:
        print("⚠️  No repositories configured in config.yaml")
        print("   Please add repositories to the 'pipeline.repositories' section")
        return
    
    clone_dir = repo_config.get('clone_dir', '/tmp/datasets')
    
    for repo in repositories:
        repo_name = repo.get('name')
        repo_url = repo.get('url')
        max_files = repo.get('max_files', None)
        
        logger.info(f"Processing repository: {repo_name}")
        
        # Clone repository if needed
        repo_path = Path(clone_dir) / repo_name.replace('/', '_')
        if not repo_path.exists():
            logger.info(f"Cloning {repo_url}...")
            try:
                RepositoryCloner.clone(repo_url, str(repo_path))
            except Exception as e:
                logger.error(f"Failed to clone {repo_url}: {e}")
                continue
        
        # Slice the repository
        try:
            slices = slicer.slice_repository(
                repo_path=str(repo_path),
                repo_name=repo_name,
                max_files=max_files
            )
            logger.info(f"Generated {len(slices)} slices from {repo_name}")
        except Exception as e:
            logger.error(f"Failed to slice {repo_name}: {e}")
    
    # Export slices
    slices_file = slicer.export_slices()
    stats = slicer.get_statistics()
    
    print(f"\n✓ Slicing complete!")
    print(f"  Total slices: {stats['total_slices']}")
    print(f"  By type: {stats['by_type']}")
    print(f"  By complexity: {stats['by_complexity']}")
    print(f"  Output: {slices_file}")
    
    print("\n⚠️  MANUAL REVIEW CHECKPOINT 1 / 人工审核检查点1")
    print(f"   Review: {slices_file}")
    print(f"   Move approved slices to '{pipeline_config.get('reviewed_slices_dir', 'reviewed_slices')}/'")
    
    # ========================================================================
    # STAGE 3: Batch Processing Preparation
    # 阶段3：批处理准备
    # ========================================================================
    print("\n[STAGE 3] Batch Processing Preparation / 批处理准备")
    print("-" * 60)
    
    processor = BatchProcessor(
        config_path="llm_config.yaml",
        output_dir=batch_input_dir
    )
    
    # Load slices (for demo, use original slices)
    import json
    with open(slices_file, 'r') as f:
        all_slices = [json.loads(line) for line in f if line.strip()]
    
    # Split by scenario according to config
    scenario_split = pipeline_config.get('scenario_split', {})
    scenario1_types = scenario_split.get('scenario1_types', ['function'])
    scenario2_types = scenario_split.get('scenario2_types', ['class'])
    
    max_scenario1 = pipeline_config.get('max_scenario1_items', 100)
    max_scenario2 = pipeline_config.get('max_scenario2_items', 50)
    
    scenario1_slices = [s for s in all_slices if s['type'] in scenario1_types][:max_scenario1]
    scenario2_slices = [s for s in all_slices if s['type'] in scenario2_types][:max_scenario2]
    
    print(f"✓ Scenario 1 slices: {len(scenario1_slices)}")
    print(f"✓ Scenario 2 slices: {len(scenario2_slices)}")
    
    # Create batch requests
    if scenario1_slices:
        requests = processor.create_scenario1_prompts(scenario1_slices)
        batch_file_1 = processor.export_batch_requests(requests, "scenario1")
        print(f"✓ Scenario 1 batch file: {batch_file_1}")
    
    if scenario2_slices:
        requests = processor.create_scenario2_prompts(scenario2_slices)
        batch_file_2 = processor.export_batch_requests(requests, "scenario2")
        print(f"✓ Scenario 2 batch file: {batch_file_2}")
    
    print("\n📝 Next: Submit batch files to OpenAI Batch API")
    print("   See PIPELINE.md for detailed instructions")
    
    # ========================================================================
    # STAGE 5: Dataset Compilation (simulated)
    # 阶段5：数据集编译（模拟）
    # ========================================================================
    print("\n[STAGE 5] Dataset Compilation (Simulated) / 数据集编译（模拟）")
    print("-" * 60)
    print("NOTE: This requires actual batch API responses.")
    print("      Creating dummy data for demonstration.")
    
    # Create dummy response files
    batch_output_dir = pipeline_config.get('batch_output_dir', 'batch_output')
    Path(batch_output_dir).mkdir(exist_ok=True)
    
    # Create minimal dummy data
    dummy_scenario1 = [{
        'id': 'demo_1',
        'question': 'Demo question',
        'answer': 'Demo answer',
        'reasoning_trace': {'steps': [], 'conclusion': 'demo'},
        'repository': 'demo/repo'
    }]
    
    dummy_scenario2 = [{
        'id': 'demo_2',
        'requirement': {'title': 'Demo'},
        'design_solution': {'overview': 'Demo', 'architecture': {'style': 'Demo'}},
        'reasoning_trace': {'decision_points': []},
        'repository': 'demo/repo'
    }]
    
    scenario1_response = Path(batch_output_dir) / 'scenario1_responses.jsonl'
    scenario2_response = Path(batch_output_dir) / 'scenario2_responses.jsonl'
    
    with open(scenario1_response, 'w') as f:
        for item in dummy_scenario1:
            f.write(json.dumps(item) + '\n')
    
    with open(scenario2_response, 'w') as f:
        for item in dummy_scenario2:
            f.write(json.dumps(item) + '\n')
    
    # Compile dataset
    compiler = DatasetCompiler(output_dir=final_output_dir)
    compiler.load_scenario_data(
        scenario1_file=str(scenario1_response),
        scenario2_file=str(scenario2_response)
    )
    
    # Export with configured settings
    shuffle = pipeline_config.get('shuffle_dataset', True)
    seed = pipeline_config.get('random_seed', 42)
    
    training_file = compiler.export_training_dataset(shuffle=shuffle, seed=seed)
    stats_file = compiler.export_statistics()
    summary_file = compiler.create_review_summary()
    
    print(f"\n✅ Pipeline Complete!")
    print(f"   Training dataset: {training_file}")
    print(f"   Statistics: {stats_file}")
    print(f"   Review summary: {summary_file}")
    
    print("\n📊 Quick Statistics:")
    stats = compiler.generate_statistics()
    print(f"   Scenario 1: {stats['scenario1']['total_count']} items")
    print(f"   Scenario 2: {stats['scenario2']['total_count']} items")
    print(f"   Total: {stats['combined']['total_items']} items")


if __name__ == "__main__":
    main()

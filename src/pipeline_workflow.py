"""
Pipeline Workflow - Automated End-to-End Training Dataset Generation
自动化端到端训练数据集生成流水线

This workflow automates the entire process from code slicing to dataset compilation,
skipping the manual review stage for direct processing.
此工作流自动化了从代码切片到数据集编译的整个过程，跳过人工审核阶段直接进行处理。
"""

import sys
import logging
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.code_slicer import CodeSlicer
from src.pipeline.scenario_processor import ScenarioProcessor
from src.pipeline.batch_submitter import BatchSubmitter
from src.pipeline.dataset_compiler import DatasetCompiler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PipelineWorkflow")

def main():
    # 1. Configuration / 配置
    # ========================================================================
    REPOS_ROOT = Path("data/0.cloned_repo")
    SLICES_ROOT = Path("data/1.slices")
    BATCH_INPUT_ROOT = Path("data/3.batch_input")
    BATCH_OUTPUT_ROOT = Path("data/4.batch_output")
    FINAL_OUTPUT_ROOT = Path("data/5.final_output")
    
    CONFIG_PATH = "config.json"
    MAX_FILES_PER_REPO = 100 # Adjust as needed
    
    # Ensure directories exist
    for d in [SLICES_ROOT, BATCH_INPUT_ROOT, BATCH_OUTPUT_ROOT, FINAL_OUTPUT_ROOT]:
        d.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("🚀 Elephenotype: Training Dataset Generation Pipeline")
    print("🚀 Elephenotype: 训练数据集生成流水线 (自动化版)")
    print("=" * 70)

    # 2. STAGE 1: Code Slicing / 代码切片
    # ========================================================================
    print(f"\n[STAGE 1] Code Slicing / 代码切片")
    print("-" * 70)
    
    repo_dirs = [d for d in REPOS_ROOT.iterdir() if d.is_dir()]
    if not repo_dirs:
        logger.error(f"No repositories found in {REPOS_ROOT}. Please clone some repos first.")
        return

    slicer = CodeSlicer()
    all_slices_paths = []

    for repo_path in repo_dirs:
        repo_name = repo_path.name
        logger.info(f"Slicing repository: {repo_name}")
        
        # Slice repository
        repo_slices = slicer.slice_repository(
            repo_path=str(repo_path),
            repo_name=repo_name,
            max_files=MAX_FILES_PER_REPO
        )
        
        # Export to data/1.slices/{repo_name}/code_slices.jsonl
        repo_output_dir = SLICES_ROOT / repo_name
        repo_output_dir.mkdir(parents=True, exist_ok=True)
        slices_file = slicer.export_slices(output_file=repo_output_dir / "code_slices.jsonl")
        all_slices_paths.append(slices_file)
        
        # Clear slicer's internal state for next repo
        slicer.slices = []

    # 3. STAGE 2: Scenario Processing / 场景处理 (跳过人工审核)
    # ========================================================================
    # 直接使用 data/1.slices 作为输入，跳过 data/2.reviewed_slices
    print(f"\n[STAGE 2] Scenario Processing / 场景处理 (Skipping Manual Review)")
    print("-" * 70)
    
    processor = ScenarioProcessor(config_path=CONFIG_PATH)
    
    for repo_name in [d.name for d in repo_dirs]:
        logger.info(f"Processing scenarios for: {repo_name}")
        
        # Use slices from Stage 1 directly
        repo_slices_dir = SLICES_ROOT / repo_name
        repo_batch_input_dir = BATCH_INPUT_ROOT / repo_name
        repo_batch_input_dir.mkdir(parents=True, exist_ok=True)
        
        # Update processor output dir for this repo
        processor.output_dir = repo_batch_input_dir
        
        # Process slices into batch inputs
        # Note: We pass SLICES_ROOT/{repo_name} as the "reviewed" directory
        batch_files = processor.process_reviewed_slices(
            reviewed_slices_dir=str(repo_slices_dir),
            max_scenario1=200, # Example limits
            max_scenario2=100
        )
        logger.info(f"Generated batch inputs for {repo_name}: {list(batch_files.keys())}")

    # 4. STAGE 3: Batch Submission / 批处理提交
    # ========================================================================
    print(f"\n[STAGE 3] Batch Submission / 批处理提交")
    print("-" * 70)
    
    # Check if config has API key
    try:
        submitter = BatchSubmitter(config_path=CONFIG_PATH)
        user_input = input("Do you want to submit these batches to OpenAI now? (y/n): ")
        
        if user_input.lower() == 'y':
            for repo_name in [d.name for d in repo_dirs]:
                repo_input_dir = BATCH_INPUT_ROOT / repo_name
                repo_output_dir = BATCH_OUTPUT_ROOT / repo_name
                
                logger.info(f"Submitting batches for {repo_name}...")
                submission_results = submitter.submit_batch_files(
                    batch_input_dir=str(repo_input_dir),
                    output_dir=str(repo_output_dir)
                )
                logger.info(f"Submitted {len(submission_results['submitted_jobs'])} jobs for {repo_name}")
        else:
            print("Skipping submission. You can submit later using:")
            print("python src/pipeline/batch_submitter.py")
    except Exception as e:
        logger.error(f"Batch submission setup failed (possibly missing config.json or API key): {e}")
        print("Skipping automatic submission.")

    # 5. STAGE 4: Dataset Compilation / 数据集编译
    # ========================================================================
    print(f"\n[STAGE 4] Dataset Compilation / 数据集编译")
    print("-" * 70)
    print("NOTE: This stage requires batch results in data/4.batch_output.")
    
    # We check if there are any results to compile
    output_files = list(BATCH_OUTPUT_ROOT.rglob("scenario*_output.jsonl"))
    
    if not output_files:
        print("No batch results found in data/4.batch_output.")
        print("Please download results after they are processed by OpenAI and place them in the directory structure:")
        print("data/4.batch_output/{repo_name}/scenarioX_output.jsonl")
    else:
        logger.info(f"Found {len(output_files)} result files. Starting compilation...")
        
        # DatasetCompiler uses source_data_dir for mapping
        # Since we skipped manual review, we point it to SLICES_ROOT (data/1.slices)
        compiler = DatasetCompiler(
            output_dir=str(FINAL_OUTPUT_ROOT),
            source_data_dir=str(SLICES_ROOT)
        )
        
        results = compiler.process_all_outputs(
            batch_output_dir=str(BATCH_OUTPUT_ROOT),
            train_ratio=0.8,
            val_ratio=0.2
        )
        
        print("\n✅ Compilation Complete!")
        print(f"   Train Dataset: {results['unified_datasets']['train']}")
        print(f"   Val Dataset:   {results['unified_datasets']['val']}")
        print(f"   Statistics:    {results['statistics_file']}")
        print(f"   Summary:       {results['summary_file']}")

    print("\n" + "=" * 70)
    print("🏁 Workflow execution finished / 工作流执行完毕")
    print("=" * 70)

if __name__ == "__main__":
    main()

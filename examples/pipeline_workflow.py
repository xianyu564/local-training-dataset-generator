"""
Pipeline Workflow Example - Complete End-to-End Process
流水线工作流示例 - 完整的端到端过程

This example demonstrates the complete pipeline from code slicing to final dataset compilation.
此示例演示从代码切片到最终数据集编译的完整流水线。
"""

import logging
from pathlib import Path

from src.pipeline.code_slicer import CodeSlicer
from src.pipeline.batch_processor import BatchProcessor
from src.pipeline.dataset_compiler import DatasetCompiler
from src.analyzers.code_analyzer import RepositoryCloner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main pipeline workflow"""
    
    # Configuration
    # 配置
    REPOS = [
        {
            "url": "https://github.com/nsidnev/fastapi-realworld-example-app.git",
            "name": "nsidnev/fastapi-realworld-example-app"
        },
        # Add more repositories as needed
        # 根据需要添加更多仓库
    ]
    
    CLONE_DIR = "/tmp/datasets"
    MAX_FILES_PER_REPO = 20  # Limit for demonstration
    
    print("=" * 60)
    print("Training Dataset Generation Pipeline")
    print("训练数据集生成流水线")
    print("=" * 60)
    
    # ========================================================================
    # STAGE 1: Code Slicing
    # 阶段1：代码切片
    # ========================================================================
    print("\n[STAGE 1] Code Slicing / 代码切片")
    print("-" * 60)
    
    slicer = CodeSlicer(output_dir="slices")
    
    for repo in REPOS:
        logger.info(f"Processing repository: {repo['name']}")
        
        # Clone repository if needed
        # 如果需要，克隆仓库
        repo_path = Path(CLONE_DIR) / repo['name'].replace('/', '_')
        if not repo_path.exists():
            logger.info(f"Cloning {repo['url']}...")
            RepositoryCloner.clone(repo['url'], str(repo_path))
        
        # Slice the repository
        # 切片仓库
        slices = slicer.slice_repository(
            repo_path=str(repo_path),
            repo_name=repo['name'],
            max_files=MAX_FILES_PER_REPO
        )
        logger.info(f"Generated {len(slices)} slices from {repo['name']}")
    
    # Export slices to JSONL
    # 导出切片到JSONL
    slices_file = slicer.export_slices()
    logger.info(f"Slices exported to: {slices_file}")
    
    # Show statistics
    # 显示统计信息
    stats = slicer.get_statistics()
    print("\nSlicing Statistics / 切片统计:")
    print(f"  Total slices: {stats['total_slices']}")
    print(f"  By type: {stats['by_type']}")
    print(f"  By complexity: {stats['by_complexity']}")
    
    print("\n⚠️  MANUAL REVIEW CHECKPOINT 1 / 人工审核检查点1")
    print("   Please review the slices at:", slices_file)
    print("   Move reviewed slices to 'reviewed_slices/' directory")
    print("   请审核切片文件:", slices_file)
    print("   将审核后的切片移至 'reviewed_slices/' 目录")
    
    # ========================================================================
    # STAGE 2: Manual Review (simulated - in practice, user does this)
    # 阶段2：人工审核（模拟 - 实践中由用户完成）
    # ========================================================================
    print("\n[STAGE 2] Manual Review / 人工审核")
    print("-" * 60)
    print("In practice, you would:")
    print("1. Review slices in 'slices/' directory")
    print("2. Filter or modify as needed")
    print("3. Save approved slices to 'reviewed_slices/'")
    print("\n实践中，您需要：")
    print("1. 审核 'slices/' 目录中的切片")
    print("2. 根据需要过滤或修改")
    print("3. 将批准的切片保存到 'reviewed_slices/'")
    
    # For demo purposes, we'll use the original slices
    # 为演示目的，我们将使用原始切片
    reviewed_slices_file = slices_file
    
    # ========================================================================
    # STAGE 3: Batch Processing Preparation
    # 阶段3：批处理准备
    # ========================================================================
    print("\n[STAGE 3] Batch Processing Preparation / 批处理准备")
    print("-" * 60)
    
    processor = BatchProcessor(
        config_path="llm_config.yaml",
        output_dir="batch_input"
    )
    
    # Load reviewed slices
    # 加载审核后的切片
    with open(reviewed_slices_file, 'r') as f:
        import json
        reviewed_slices = [json.loads(line) for line in f if line.strip()]
    
    # Split slices for different scenarios
    # 为不同场景分割切片
    # For Scenario 1: Use function slices (Q&A works better with functions)
    # 场景1：使用函数切片（问答更适合函数）
    scenario1_slices = [s for s in reviewed_slices if s['type'] == 'function'][:10]
    
    # For Scenario 2: Use class slices (Design works better with classes)
    # 场景2：使用类切片（设计更适合类）
    scenario2_slices = [s for s in reviewed_slices if s['type'] == 'class'][:5]
    
    logger.info(f"Scenario 1 slices: {len(scenario1_slices)}")
    logger.info(f"Scenario 2 slices: {len(scenario2_slices)}")
    
    # Create batch requests for Scenario 1
    # 为场景1创建批处理请求
    scenario1_requests = processor.create_scenario1_prompts(scenario1_slices)
    scenario1_batch_file = processor.export_batch_requests(
        scenario1_requests, 
        scenario="scenario1"
    )
    logger.info(f"Scenario 1 batch requests exported to: {scenario1_batch_file}")
    
    # Create batch requests for Scenario 2
    # 为场景2创建批处理请求
    scenario2_requests = processor.create_scenario2_prompts(scenario2_slices)
    scenario2_batch_file = processor.export_batch_requests(
        scenario2_requests,
        scenario="scenario2"
    )
    logger.info(f"Scenario 2 batch requests exported to: {scenario2_batch_file}")
    
    print("\n📝 Next Steps for Batch Processing:")
    print("1. Upload batch files to OpenAI Batch API")
    print("2. Wait for processing (typically 24h)")
    print("3. Download results to 'batch_output/' directory")
    print("\n📝 批处理的后续步骤：")
    print("1. 将批处理文件上传到OpenAI批处理API")
    print("2. 等待处理（通常24小时）")
    print("3. 将结果下载到 'batch_output/' 目录")
    
    # ========================================================================
    # STAGE 4: Manual Review of Generated Data (in practice)
    # 阶段4：生成数据的人工审核（实践中）
    # ========================================================================
    print("\n[STAGE 4] Manual Review of Generated Data / 生成数据的人工审核")
    print("-" * 60)
    print("After batch processing completes:")
    print("1. Review the generated Q&A pairs and design solutions")
    print("2. Filter out low-quality items")
    print("3. Keep approved items for final compilation")
    print("\n批处理完成后：")
    print("1. 审核生成的问答对和设计方案")
    print("2. 过滤掉低质量项目")
    print("3. 保留批准的项目用于最终编译")
    
    # ========================================================================
    # STAGE 5: Dataset Compilation (simulated with dummy data)
    # 阶段5：数据集编译（使用虚拟数据模拟）
    # ========================================================================
    print("\n[STAGE 5] Dataset Compilation / 数据集编译")
    print("-" * 60)
    print("NOTE: This stage requires actual batch API responses.")
    print("For demonstration, we'll create dummy response files.")
    print("\n注意：此阶段需要实际的批处理API响应。")
    print("为演示目的，我们将创建虚拟响应文件。")
    
    # Create dummy response files for demonstration
    # 为演示创建虚拟响应文件
    _create_dummy_responses()
    
    # Compile the dataset
    # 编译数据集
    compiler = DatasetCompiler(output_dir="final_output")
    
    # Load scenario data (if exists)
    # 加载场景数据（如果存在）
    scenario1_response = "batch_output/scenario1_responses.jsonl"
    scenario2_response = "batch_output/scenario2_responses.jsonl"
    
    if Path(scenario1_response).exists() and Path(scenario2_response).exists():
        compiler.load_scenario_data(
            scenario1_file=scenario1_response,
            scenario2_file=scenario2_response
        )
        
        # Generate statistics
        # 生成统计信息
        stats_file = compiler.export_statistics()
        logger.info(f"Statistics exported to: {stats_file}")
        
        # Export training dataset
        # 导出训练数据集
        training_file = compiler.export_training_dataset(shuffle=True, seed=42)
        logger.info(f"Training dataset exported to: {training_file}")
        
        # Create review summary
        # 创建审核摘要
        summary_file = compiler.create_review_summary()
        logger.info(f"Review summary created at: {summary_file}")
        
        print("\n✅ Pipeline Complete! / 流水线完成！")
        print(f"   Training dataset: {training_file}")
        print(f"   Statistics: {stats_file}")
        print(f"   Review summary: {summary_file}")
    else:
        print("\n⚠️  Batch response files not found. Skipping compilation.")
        print("   Please process batch requests and place responses in batch_output/")
        print("\n⚠️  未找到批处理响应文件。跳过编译。")
        print("   请处理批处理请求并将响应放在 batch_output/ 中")


def _create_dummy_responses():
    """Create dummy response files for demonstration"""
    import json
    from pathlib import Path
    
    output_dir = Path("batch_output")
    output_dir.mkdir(exist_ok=True)
    
    # Dummy Scenario 1 response
    scenario1_data = [
        {
            "id": "scenario1_test_00001",
            "scenario": "scenario1",
            "question": "What does this function do?",
            "answer": "This function processes data...",
            "reasoning_trace": {
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Analyze function signature",
                        "code_reference": "def process_data()",
                        "reasoning": "Identifies the function purpose"
                    }
                ],
                "conclusion": "Function performs data processing"
            },
            "business_rules": ["Validates input data"]
        }
    ]
    
    with open(output_dir / "scenario1_responses.jsonl", 'w') as f:
        for item in scenario1_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Dummy Scenario 2 response
    scenario2_data = [
        {
            "id": "scenario2_test_00001",
            "scenario": "scenario2",
            "requirement": {
                "title": "User authentication",
                "description": "Implement secure user login",
                "constraints": ["Must be RESTful"]
            },
            "design_solution": {
                "overview": "JWT-based authentication",
                "architecture": {
                    "style": "Layered",
                    "components": ["AuthController", "TokenService"],
                    "data_flow": "Client -> API -> Database"
                }
            },
            "reasoning_trace": {
                "decision_points": [
                    {
                        "decision": "Use JWT tokens",
                        "rationale": "Stateless and scalable"
                    }
                ]
            }
        }
    ]
    
    with open(output_dir / "scenario2_responses.jsonl", 'w') as f:
        for item in scenario2_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


if __name__ == "__main__":
    main()

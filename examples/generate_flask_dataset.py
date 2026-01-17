"""
Example: Generate Training Dataset from Flask Repository
示例：从Flask仓库生成训练数据集

This example demonstrates how to use the training dataset generator
with the popular Flask web framework repository.
此示例演示如何使用训练数据集生成器与流行的Flask Web框架仓库。
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dataset_generator.core import DatasetGenerator
from src.utils.dataset_utils import (
    validate_dataset, 
    calculate_diversity_score,
    generate_statistics_report,
    split_train_test
)
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function"""
    
    # Configuration
    # Use Flask repository as example
    REPO_URL = "https://github.com/pallets/flask.git"
    REPO_NAME = "pallets/flask"
    CLONE_DIR = "/tmp/datasets"
    OUTPUT_DIR = "./output/flask_dataset"
    
    logger.info("=" * 80)
    logger.info("Training Dataset Generator - Example with Flask Repository")
    logger.info("训练数据集生成器 - Flask仓库示例")
    logger.info("=" * 80)
    
    # Step 1: Clone and initialize
    logger.info("\nStep 1: Cloning repository...")
    logger.info("步骤1：克隆仓库...")
    
    try:
        generator = DatasetGenerator.from_github_url(
            repo_url=REPO_URL,
            clone_dir=CLONE_DIR,
            repo_name=REPO_NAME
        )
    except Exception as e:
        logger.error(f"Failed to clone repository: {e}")
        # If already exists, use it
        repo_path = Path(CLONE_DIR) / REPO_NAME.replace('/', '_')
        if repo_path.exists():
            logger.info("Using existing repository")
            generator = DatasetGenerator(str(repo_path), REPO_NAME)
        else:
            raise
    
    # Step 2: Analyze repository
    logger.info("\nStep 2: Analyzing repository...")
    logger.info("步骤2：分析仓库...")
    
    generator.analyze_repository(max_files=20)  # Limit to 20 files for example
    
    # Show statistics
    stats = generator.get_statistics()
    logger.info(f"\nRepository Statistics / 仓库统计:")
    logger.info(f"  Total modules: {stats['total_modules']}")
    logger.info(f"  Total functions: {stats['total_functions']}")
    logger.info(f"  Total classes: {stats['total_classes']}")
    logger.info(f"  Functions by complexity:")
    for complexity, count in stats['functions_by_complexity'].items():
        logger.info(f"    {complexity}: {count}")
    
    # Step 3: Generate Scenario 1 Dataset (Q&A Pairs)
    logger.info("\nStep 3: Generating Scenario 1 Dataset (Q&A Pairs)...")
    logger.info("步骤3：生成场景1数据集（问答对）...")
    
    qa_pairs = generator.generate_scenario1_dataset(
        max_pairs=20,  # Generate 20 pairs per language
        languages=["en", "zh"]
    )
    
    logger.info(f"Generated {len(qa_pairs)} Q&A pairs")
    
    # Show sample Q&A
    if qa_pairs:
        logger.info("\nSample Q&A Pair (English) / 示例问答对（英语）:")
        sample_en = next((qa for qa in qa_pairs if qa.language == "en"), None)
        if sample_en:
            logger.info(f"  Q: {sample_en.question}")
            logger.info(f"  A: {sample_en.answer[:100]}...")
            logger.info(f"  Reasoning steps: {len(sample_en.reasoning_trace.steps)}")
    
    # Step 4: Generate Scenario 2 Dataset (Design Solutions)
    logger.info("\nStep 4: Generating Scenario 2 Dataset (Design Solutions)...")
    logger.info("步骤4：生成场景2数据集（设计方案）...")
    
    solutions = generator.generate_scenario2_dataset(
        max_solutions=4,  # Generate 2 solutions per language
        languages=["en", "zh"]
    )
    
    logger.info(f"Generated {len(solutions)} design solutions")
    
    # Show sample solution
    if solutions:
        logger.info("\nSample Design Solution (English) / 示例设计方案（英语）:")
        sample_sol = next((sol for sol in solutions if sol.language == "en"), None)
        if sample_sol:
            logger.info(f"  Requirement: {sample_sol.requirement.title}")
            logger.info(f"  Architecture: {sample_sol.design_solution.architecture.style}")
            logger.info(f"  Components: {len(sample_sol.design_solution.architecture.components)}")
            logger.info(f"  Decision points: {len(sample_sol.reasoning_trace.decision_points)}")
    
    # Step 5: Export datasets
    logger.info("\nStep 5: Exporting datasets...")
    logger.info("步骤5：导出数据集...")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generator.export_dataset(
        output_dir=OUTPUT_DIR,
        qa_pairs=qa_pairs,
        solutions=solutions,
        split_by_language=True
    )
    
    # Step 6: Validate and generate report
    logger.info("\nStep 6: Validating dataset and generating report...")
    logger.info("步骤6：验证数据集并生成报告...")
    
    # Combine all items for validation
    all_items = [qa.to_dict() for qa in qa_pairs] + [sol.to_dict() for sol in solutions]
    
    # Validate
    validation_results = validate_dataset(all_items)
    logger.info(f"\nValidation Results / 验证结果:")
    logger.info(f"  Total items: {validation_results['total_items']}")
    logger.info(f"  Valid items: {validation_results['valid_items']}")
    logger.info(f"  Invalid items: {validation_results['invalid_items']}")
    logger.info(f"  Validity rate: {validation_results['validity_rate']:.2%}")
    
    # Diversity score
    diversity = calculate_diversity_score(all_items)
    logger.info(f"\nDiversity Score / 多样性分数: {diversity:.2%}")
    
    # Generate comprehensive report
    report = generate_statistics_report(all_items)
    report_file = Path(OUTPUT_DIR) / "dataset_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info(f"Report saved to {report_file}")
    
    # Step 7: Split train/test
    logger.info("\nStep 7: Splitting into train/test sets...")
    logger.info("步骤7：分割训练集和测试集...")
    
    train_set, test_set = split_train_test(all_items, test_ratio=0.2)
    
    train_file = Path(OUTPUT_DIR) / "train_dataset.json"
    test_file = Path(OUTPUT_DIR) / "test_dataset.json"
    
    with open(train_file, 'w', encoding='utf-8') as f:
        json.dump(train_set, f, indent=2, ensure_ascii=False)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_set, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Train set: {len(train_set)} items -> {train_file}")
    logger.info(f"Test set: {len(test_set)} items -> {test_file}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY / 摘要")
    logger.info("=" * 80)
    logger.info(f"✓ Repository analyzed: {REPO_NAME}")
    logger.info(f"✓ Q&A pairs generated: {len(qa_pairs)}")
    logger.info(f"✓ Design solutions generated: {len(solutions)}")
    logger.info(f"✓ Total dataset items: {len(all_items)}")
    logger.info(f"✓ Validation rate: {validation_results['validity_rate']:.2%}")
    logger.info(f"✓ Diversity score: {diversity:.2%}")
    logger.info(f"✓ Output directory: {OUTPUT_DIR}")
    logger.info("=" * 80)
    logger.info("\n✓ Dataset generation complete! / 数据集生成完成！")


if __name__ == "__main__":
    main()

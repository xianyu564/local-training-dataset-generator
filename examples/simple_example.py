"""
Simple Example: Generate Dataset from Local Code
简单示例：从本地代码生成数据集

This example demonstrates generating a dataset from the project itself.
此示例演示从项目本身生成数据集。
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dataset_generator.core import DatasetGenerator
from src.utils.dataset_utils import generate_statistics_report
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Generate dataset from this project itself"""
    
    logger.info("=" * 80)
    logger.info("Simple Example: Generate Dataset from This Project")
    logger.info("简单示例：从本项目生成数据集")
    logger.info("=" * 80)
    
    # Use the current project as the repository
    project_root = Path(__file__).parent.parent
    
    logger.info(f"\nAnalyzing project at: {project_root}")
    
    # Initialize generator
    generator = DatasetGenerator(
        repo_path=str(project_root),
        repo_name="local-training-dataset-generator"
    )
    
    # Analyze repository (limit to 10 files for quick demo)
    logger.info("\n1. Analyzing repository...")
    generator.analyze_repository(max_files=10)
    
    # Show statistics
    stats = generator.get_statistics()
    logger.info(f"\nRepository Statistics:")
    logger.info(f"  Modules: {stats['total_modules']}")
    logger.info(f"  Functions: {stats['total_functions']}")
    logger.info(f"  Classes: {stats['total_classes']}")
    
    # Generate Scenario 1 dataset
    logger.info("\n2. Generating Q&A pairs...")
    qa_pairs = generator.generate_scenario1_dataset(
        max_pairs=5,
        languages=["en", "zh"]
    )
    logger.info(f"Generated {len(qa_pairs)} Q&A pairs")
    
    # Generate Scenario 2 dataset
    logger.info("\n3. Generating design solutions...")
    solutions = generator.generate_scenario2_dataset(
        max_solutions=2,
        languages=["en", "zh"]
    )
    logger.info(f"Generated {len(solutions)} design solutions")
    
    # Export
    output_dir = project_root / "output" / "simple_example"
    logger.info(f"\n4. Exporting to {output_dir}")
    generator.export_dataset(
        output_dir=str(output_dir),
        qa_pairs=qa_pairs,
        solutions=solutions,
        split_by_language=True
    )
    
    # Generate report
    all_items = [qa.to_dict() for qa in qa_pairs] + [sol.to_dict() for sol in solutions]
    report = generate_statistics_report(all_items)
    
    logger.info("\n5. Dataset Report:")
    logger.info(f"  Total items: {report['total_items']}")
    logger.info(f"  By type: {report['by_type']}")
    logger.info(f"  By language: {report['by_language']}")
    logger.info(f"  Diversity score: {report['diversity_score']:.2%}")
    logger.info(f"  Validation: {report['validation']['validity_rate']:.2%} valid")
    
    # Show sample Q&A
    if qa_pairs:
        logger.info("\n" + "=" * 80)
        logger.info("Sample Q&A Pair (English)")
        logger.info("=" * 80)
        sample = next((qa for qa in qa_pairs if qa.language == "en"), qa_pairs[0])
        logger.info(f"\nQuestion: {sample.question}")
        logger.info(f"\nAnswer: {sample.answer}")
        logger.info(f"\nCode Context:")
        logger.info(f"  File: {sample.code_context.file_path}")
        logger.info(f"  Function: {sample.code_context.function_name}")
        logger.info(f"  Lines: {sample.code_context.start_line}-{sample.code_context.end_line}")
        logger.info(f"\nReasoning Steps: {len(sample.reasoning_trace.steps)}")
        for step in sample.reasoning_trace.steps[:2]:  # Show first 2 steps
            logger.info(f"  Step {step.step_number}: {step.description}")
    
    # Show sample design solution
    if solutions:
        logger.info("\n" + "=" * 80)
        logger.info("Sample Design Solution (English)")
        logger.info("=" * 80)
        sample = next((sol for sol in solutions if sol.language == "en"), solutions[0])
        logger.info(f"\nRequirement: {sample.requirement.title}")
        logger.info(f"Description: {sample.requirement.description}")
        logger.info(f"\nArchitecture Style: {sample.design_solution.architecture.style}")
        logger.info(f"Components: {len(sample.design_solution.architecture.components)}")
        for comp in sample.design_solution.architecture.components[:2]:
            logger.info(f"  - {comp.name}: {comp.responsibility}")
    
    logger.info("\n" + "=" * 80)
    logger.info("✓ Generation complete! Check output directory for full datasets.")
    logger.info("✓ 生成完成！查看输出目录以获取完整数据集。")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

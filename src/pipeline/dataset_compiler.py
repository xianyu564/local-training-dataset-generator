"""
Dataset Compiler - Compile OpenAI batch outputs into training datasets
数据集编译器 - 将OpenAI批处理输出编译为训练数据集

This module processes data/4.batch_output files into organized training datasets.
该模块将 data/4.batch_output 文件处理为组织化的训练数据集。
"""

import json
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetCompiler:
    """
    Dataset Compiler for organizing and compiling training datasets from OpenAI outputs
    从OpenAI输出组织和编译训练数据集的编译器
    """

    def __init__(self, output_dir: str = "data/5.final_output", source_data_dir: str = "data/2.reviewed_slices"):
        """
        Initialize DatasetCompiler

        Args:
            output_dir: Directory to save final datasets
            source_data_dir: Directory containing original reviewed slices
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.source_data_dir = Path(source_data_dir)

        # Data organized by repository and scenario
        self.repo_data: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
        self.all_data: List[Dict[str, Any]] = []
        
        # Source data for mapping custom_id back to original context
        self.source_data: Dict[str, Dict[str, Any]] = {}

    def load_source_data(self) -> None:
        """Load original reviewed slices to correlate with batch outputs"""
        if not self.source_data_dir.exists():
            logger.warning(f"Source data directory not found: {self.source_data_dir}")
            return

        slice_files = list(self.source_data_dir.rglob("code_slices.jsonl"))
        logger.info(f"Loading source data from {len(slice_files)} files...")

        for slice_file in slice_files:
            data = self._load_jsonl(str(slice_file))
            for item in data:
                if 'id' in item:
                    self.source_data[item['id']] = item
        
        logger.info(f"Loaded {len(self.source_data)} source slices for mapping")
    
    def scan_and_load_batch_outputs(self, batch_output_dir: str = "data/4.batch_output") -> None:
        """
        Scan and load all batch output files from data/4.batch_output
        扫描并加载 data/4.batch_output 中的所有批处理输出文件

        Args:
            batch_output_dir: Directory containing batch output files
        """
        batch_dir = Path(batch_output_dir)
        if not batch_dir.exists():
            raise FileNotFoundError(f"Batch output directory not found: {batch_dir}")

        # Find all scenario output files (exclude archive directory)
        pattern = "**/scenario*_output.jsonl"
        output_files = list(batch_dir.glob(pattern))

        # Filter out files in archive directory
        output_files = [f for f in output_files if "archive" not in str(f)]

        logger.info(f"Found {len(output_files)} batch output files")

        total_items = 0
        for output_file in output_files:
            # Extract repo name from path
            repo_name = self._extract_repo_name(output_file)

            # Determine scenario
            scenario = self._extract_scenario(output_file)

            # Load data
            data = self._load_jsonl(str(output_file))

            # Store by repo and scenario
            self.repo_data[repo_name][scenario].extend(data)
            self.all_data.extend(data)

            logger.info(f"Loaded {len(data)} items from {output_file} (repo: {repo_name}, scenario: {scenario})")
            total_items += len(data)

        logger.info(f"Total loaded {total_items} items from {len(output_files)} files")

    def process_and_export_by_repo(self) -> Dict[str, Dict[str, str]]:
        """
        Process and export organized data for each repository
        处理并导出每个仓库的组织化数据

        Returns:
            Dictionary mapping repo names to their exported files
        """
        results = {}

        for repo_name, scenarios in self.repo_data.items():
            repo_results = {}

            for scenario, data in scenarios.items():
                # Process and format the data
                processed_data = self._process_batch_output_data(data, scenario)

                # Export to repo-specific directory
                output_file = self._export_repo_scenario_data(repo_name, scenario, processed_data)
                repo_results[scenario] = output_file

            results[repo_name] = repo_results
            logger.info(f"Processed repo {repo_name}: {dict(repo_results)}")

        return results

    def create_unified_dataset(self, train_ratio: float = 0.8, val_ratio: float = 0.2,
                              random_seed: int = 42) -> Dict[str, str]:
        """
        Create unified training and validation datasets
        创建统一的训练和验证数据集

        Args:
            train_ratio: Ratio of training data
            val_ratio: Ratio of validation data
            random_seed: Random seed for shuffling

        Returns:
            Dictionary with paths to train and val files
        """
        if abs(train_ratio + val_ratio - 1.0) > 0.001:
            raise ValueError("train_ratio + val_ratio must equal 1.0")

        # Process all data
        processed_data = []
        for repo_name, scenarios in self.repo_data.items():
            for scenario, data in scenarios.items():
                processed = self._process_batch_output_data(data, scenario)
                processed_data.extend(processed)

        # Shuffle data
        random.seed(random_seed)
        random.shuffle(processed_data)

        # Split into train/val
        total_count = len(processed_data)
        train_count = int(total_count * train_ratio)
        val_count = total_count - train_count

        train_data = processed_data[:train_count]
        val_data = processed_data[train_count:train_count + val_count]

        logger.info(f"Split {total_count} items into {len(train_data)} train and {len(val_data)} val")

        # Export datasets
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        train_file = self.output_dir / f"train_dataset_{timestamp}.jsonl"
        val_file = self.output_dir / f"val_dataset_{timestamp}.jsonl"

        self._export_jsonl(train_data, train_file)
        self._export_jsonl(val_data, val_file)

        return {
            "train": str(train_file),
            "val": str(val_file)
        }

    def _build_architecture_skeleton(self, slice_data: Dict[str, Any]) -> str:
        """Build architecture skeleton from class data (same as scenario_processor)"""
        file_path = slice_data.get('file_path', 'unknown')
        name = slice_data.get('name', 'unknown')
        context = slice_data.get('context', {})

        skeleton = f"Class: {name}\nFile: {file_path}\n"
        if context.get('docstring'):
            skeleton += f"Docstring: {context.get('docstring')}\n"
        
        base_classes = context.get('base_classes', [])
        if base_classes:
            skeleton += f"Base classes: {', '.join(base_classes)}\n"

        skeleton += "\nMethods:\n"
        for method in context.get('methods', []):
            if isinstance(method, dict):
                skeleton += f"- {method.get('name', 'unknown')}()\n"
            else:
                skeleton += f"- {method}()\n"

        return skeleton

    def _format_scenario1_output(self, parsed_content: Dict[str, Any]) -> str:
        """Format Scenario 1 (QA) output for Qwen training"""
        reasoning = parsed_content.get('reasoning_trace', {})
        steps = reasoning.get('steps', [])
        
        thought_parts = []
        for step in steps:
            step_lines = []
            # Extract step number if exists
            num = step.get('step_number', step.get('step', ''))
            header = f"Step {num}" if num else "Step"
            
            # Add all other fields as content
            for key, value in step.items():
                if key in ['step_number', 'step']:
                    continue
                # Format key to be more readable (e.g. step_description -> Step Description)
                display_key = key.replace('_', ' ').title()
                step_lines.append(f"{display_key}: {value}")
            
            if step_lines:
                thought_parts.append(f"{header}:\n" + "\n".join(step_lines))
        
        conclusion = reasoning.get('conclusion', '')
        if conclusion:
            thought_parts.append(f"Conclusion: {conclusion}")
            
        thought_block = "\n\n".join(thought_parts)
        
        question = parsed_content.get('question', '')
        answer = parsed_content.get('answer', '')
        
        return f"<thought>\n{thought_block}\n</thought>\n\n初级开发者提问：{question}\n\n资深专家解答：{answer}"

    def _format_scenario2_output(self, parsed_content: Dict[str, Any]) -> str:
        """Format Scenario 2 (Design) output for Qwen training"""
        reasoning = parsed_content.get('reasoning_trace', {})
        # Scenario 2 might use 'analysis_steps' or 'steps'
        steps = reasoning.get('analysis_steps', reasoning.get('steps', []))
        
        thought_parts = []
        for step in steps:
            step_lines = []
            num = step.get('step', step.get('step_number', ''))
            header = f"Step {num}" if num else "Analysis Step"
            
            for key, value in step.items():
                if key in ['step', 'step_number']:
                    continue
                display_key = key.replace('_', ' ').title()
                step_lines.append(f"{display_key}: {value}")
            
            if step_lines:
                thought_parts.append(f"{header}:\n" + "\n".join(step_lines))
        
        rationale = reasoning.get('design_rationale', '')
        if rationale:
            thought_parts.append(f"Design Rationale: {rationale}")
            
        thought_block = "\n\n".join(thought_parts)
        
        req = parsed_content.get('requirement_analysis', {})
        design = parsed_content.get('design_solution', {})
        
        output = f"<thought>\n{thought_block}\n</thought>\n\n"
        output += f"需求分析：\n标题: {req.get('title', '')}\n描述: {req.get('description', '')}\n"
        
        output += f"\n设计方案：\n概览: {design.get('overview', '')}\n\n架构组件:\n"
        for comp in design.get('architecture', {}).get('components', []):
            output += f"- {comp}\n"
            
        output += f"\n集成点:\n"
        for pt in design.get('architecture', {}).get('integration_points', []):
            output += f"- {pt}\n"
            
        output += f"\n数据流: {design.get('architecture', {}).get('data_flow', '')}\n"
        
        output += f"\n实现计划:\n"
        for step in design.get('implementation_plan', []):
            output += f"- {step}\n"
            
        return output

    def _get_parsed_content(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and parse content from raw batch output item
        从原始批处理输出项中提取并解析内容
        """
        try:
            if 'response' in item and 'body' in item['response']:
                response_body = item['response']['body']
                if 'choices' in response_body and response_body['choices']:
                    content = response_body['choices'][0]['message']['content']
                    return json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError, TypeError):
            pass
        return None

    def _process_batch_output_data(self, data: List[Dict[str, Any]], scenario: str) -> List[Dict[str, Any]]:
        """
        Process raw batch output data into Qwen training format (instruction, input, output)
        """
        processed = []

        for item in data:
            try:
                parsed_content = self._get_parsed_content(item)
                if not parsed_content:
                    continue

                custom_id = item.get('custom_id', '')
                
                # Get source ID by removing scenario prefix
                source_id = custom_id.replace('scenario1_', '').replace('scenario2_', '')
                source_item = self.source_data.get(source_id)

                training_item = {
                    "instruction": "",
                    "input": "",
                    "output": "",
                    "metadata": {
                        "custom_id": custom_id,
                        "scenario": scenario,
                        "repo": self._extract_repo_name(Path(item.get('file_id', 'unknown'))) # Fallback
                    }
                }
                
                if source_item:
                    training_item["metadata"]["repo"] = source_item.get("repository", "unknown")

                if scenario == "scenario1":
                    training_item["instruction"] = "分析以下代码片段，并从资深开发者的角度回答一个典型的初级开发者提问。请包含详细的推理过程。"
                    if source_item:
                        training_item["input"] = f"代码路径: {source_item.get('file_path')}\n代码名称: {source_item.get('name')}\n\n代码内容:\n{source_item.get('code_snippet')}"
                    training_item["output"] = self._format_scenario1_output(parsed_content)
                
                elif scenario == "scenario2":
                    training_item["instruction"] = "基于提供的代码架构概览，为新需求设计一套技术方案。请包含详细的设计推理过程，并确保方案符合现有架构模式。"
                    if source_item:
                        skeleton = self._build_architecture_skeleton(source_item)
                        req_title = parsed_content.get('requirement_analysis', {}).get('title', '新需求')
                        req_desc = parsed_content.get('requirement_analysis', {}).get('description', '')
                        training_item["input"] = f"架构概览:\n{skeleton}\n\n需求: {req_title}\n详情: {req_desc}"
                    training_item["output"] = self._format_scenario2_output(parsed_content)
                
                processed.append(training_item)
                            
            except Exception as e:
                logger.error(f"Error processing item {item.get('custom_id', 'unknown')}: {e}")
                continue

        return processed

    def _export_repo_scenario_data(self, repo_name: str, scenario: str, data: List[Dict[str, Any]]) -> str:
        """Export processed data for a specific repo and scenario"""
        repo_dir = self.output_dir / repo_name
        repo_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = repo_dir / f"{scenario}_processed_{timestamp}.jsonl"

        self._export_jsonl(data, output_file)
        return str(output_file)

    def _export_jsonl(self, data: List[Dict[str, Any]], output_file: Path) -> None:
        """Export data to JSONL file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data:
                json_line = json.dumps(item, ensure_ascii=False)
                f.write(json_line + '\n')

        logger.info(f"Exported {len(data)} items to {output_file}")

    def _extract_repo_name(self, file_path: Path) -> str:
        """Extract repository name from file path / 从文件路径提取仓库名"""
        # Path structure: data/4.batch_output/repo_name/scenarioX_batch_xxx_output.jsonl
        parts = file_path.parts
        # Find the repo name (should be the directory containing the output file)
        for i, part in enumerate(parts):
            if part == "4.batch_output" and i + 1 < len(parts):
                return parts[i + 1]
        return "unknown_repo"

    def _extract_scenario(self, file_path: Path) -> str:
        """Extract scenario from file path / 从文件路径提取场景"""
        filename = file_path.name
        if filename.startswith("scenario1"):
            return "scenario1"
        elif filename.startswith("scenario2"):
            return "scenario2"
        else:
            return "unknown"
    
    def _load_jsonl(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data from JSONL file / 从JSONL文件加载数据"""
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse line in {file_path}: {e}")
                        continue
        return data
    
    def _calculate_percentage(self, count: int, total: int) -> float:
        """Calculate percentage safely / 安全计算百分比"""
        if total == 0:
            return 0.0
        return round(count / total * 100, 2)
    
    def generate_statistics(self) -> Dict[str, Any]:
        """
        Generate comprehensive statistics about the processed dataset
        生成处理后数据集的综合统计信息

        Returns:
            Dictionary with statistics
        """
        # Collect all processed data
        scenario1_data = []
        scenario2_data = []

        for repo_data in self.repo_data.values():
            scenario1_data.extend(repo_data.get('scenario1', []))
            scenario2_data.extend(repo_data.get('scenario2', []))

        total_items = len(scenario1_data) + len(scenario2_data)

        stats = {
            "generated_at": datetime.now().isoformat(),
            "by_repository": self._count_by_repository(),
            "scenario1": {
                "total_count": len(scenario1_data),
                "parse_success_rate": self._calculate_parse_success_rate(scenario1_data),
                "avg_reasoning_steps": self._calculate_avg_reasoning_steps(scenario1_data)
            },
            "scenario2": {
                "total_count": len(scenario2_data),
                "parse_success_rate": self._calculate_parse_success_rate(scenario2_data),
                "avg_decision_points": self._calculate_avg_decision_points(scenario2_data)
            },
            "combined": {
                "total_items": total_items,
                "scenario1_percentage": self._calculate_percentage(len(scenario1_data), total_items),
                "scenario2_percentage": self._calculate_percentage(len(scenario2_data), total_items),
                "overall_parse_success_rate": self._calculate_overall_parse_success_rate()
            }
        }

        return stats

    def _count_by_repository(self) -> Dict[str, Dict[str, int]]:
        """Count items by repository and scenario"""
        repo_counts = {}
        for repo_name, scenarios in self.repo_data.items():
            repo_counts[repo_name] = {
                "scenario1": len(scenarios.get('scenario1', [])),
                "scenario2": len(scenarios.get('scenario2', [])),
                "total": len(scenarios.get('scenario1', [])) + len(scenarios.get('scenario2', []))
            }
        return repo_counts

    def _calculate_parse_success_rate(self, data: List[Dict[str, Any]]) -> float:
        """Calculate parse success rate / 计算解析成功率"""
        if not data:
            return 0.0
        
        successful = 0
        for item in data:
            if self._get_parsed_content(item) is not None:
                successful += 1
        
        return round(successful / len(data) * 100, 2)

    def _calculate_overall_parse_success_rate(self) -> float:
        """Calculate overall parse success rate across all data / 计算总体解析成功率"""
        if not self.all_data:
            return 0.0
        
        successful = 0
        for item in self.all_data:
            if self._get_parsed_content(item) is not None:
                successful += 1
                
        return round(successful / len(self.all_data) * 100, 2)
    
    def _calculate_avg_reasoning_steps(self, data: List[Dict[str, Any]]) -> float:
        """Calculate average number of reasoning steps / 计算平均推理步骤数"""
        if not data:
            return 0.0

        total_steps = 0
        count = 0

        for item in data:
            parsed_content = self._get_parsed_content(item)
            if not parsed_content:
                continue

            reasoning_trace = parsed_content.get("reasoning_trace", {})

            # Handle different reasoning trace structures
            steps = reasoning_trace.get("steps", [])
            if not steps:  # Try analysis_steps for scenario 2
                steps = reasoning_trace.get("analysis_steps", [])

            if isinstance(steps, list):
                total_steps += len(steps)
                count += 1

        return round(total_steps / max(1, count), 2)

    def _calculate_avg_decision_points(self, data: List[Dict[str, Any]]) -> float:
        """Calculate average number of decision points / 计算平均决策点数"""
        if not data:
            return 0.0

        total_points = 0
        count = 0

        for item in data:
            parsed_content = self._get_parsed_content(item)
            if not parsed_content:
                continue

            reasoning_trace = parsed_content.get("reasoning_trace", {})

            # Handle different reasoning trace structures
            decision_points = reasoning_trace.get("decision_points", [])
            if not decision_points:  # Try analysis_steps for scenario 2
                decision_points = reasoning_trace.get("analysis_steps", [])

            if isinstance(decision_points, list):
                total_points += len(decision_points)
                count += 1

        return round(total_points / max(1, count), 2)
    
    def shuffle_and_merge_all(self, seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Shuffle and merge all processed data
        随机打乱并合并所有处理后的数据

        Args:
            seed: Random seed for reproducibility

        Returns:
            Merged and shuffled dataset
        """
        # Combine all processed data
        combined = []

        for repo_data in self.repo_data.values():
            for scenario, data in repo_data.items():
                for item in data:
                    item_copy = item.copy()
                    item_copy["training_scenario"] = f"{scenario}_processed"
                    combined.append(item_copy)

        # Shuffle
        if seed is not None:
            random.seed(seed)
        random.shuffle(combined)

        logger.info(f"Shuffled and merged {len(combined)} items")
        return combined
    
    def export_combined_dataset(self, output_file: Optional[str] = None,
                                shuffle: bool = True, seed: Optional[int] = 42) -> str:
        """
        Export combined training dataset to JSONL
        导出合并的训练数据集到JSONL

        Args:
            output_file: Output file path
            shuffle: Whether to shuffle the data
            seed: Random seed for shuffling

        Returns:
            Path to exported file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"combined_training_dataset_{timestamp}.jsonl"
        else:
            output_file = Path(output_file)

        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Get merged data
        if shuffle:
            dataset = self.shuffle_and_merge_all(seed=seed)
        else:
            dataset = self.all_data

        # Write JSONL
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in dataset:
                json_line = json.dumps(item, ensure_ascii=False)
                f.write(json_line + '\n')

        logger.info(f"Exported combined training dataset to {output_file}")
        return str(output_file)
    
    def export_statistics(self, output_file: Optional[str] = None) -> str:
        """
        Export statistics to JSON file
        导出统计信息到JSON文件
        
        Args:
            output_file: Output file path
            
        Returns:
            Path to exported file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"dataset_statistics_{timestamp}.json"
        else:
            output_file = Path(output_file)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        stats = self.generate_statistics()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported statistics to {output_file}")
        return str(output_file)
    
    def create_review_summary(self, output_file: Optional[str] = None) -> str:
        """
        Create a human-readable summary for review
        创建人类可读的审核摘要
        
        Args:
            output_file: Output file path
            
        Returns:
            Path to exported file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"review_summary_{timestamp}.md"
        else:
            output_file = Path(output_file)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        stats = self.generate_statistics()
        
        summary = f"""# Training Dataset Review Summary
# 训练数据集审核摘要

Generated: {stats['generated_at']}

## Overview / 概览

- **Total Items**: {stats['combined']['total_items']}
- **Scenario 1 (Q&A)**: {stats['scenario1']['total_count']} ({stats['combined']['scenario1_percentage']}%)
- **Scenario 2 (Design)**: {stats['scenario2']['total_count']} ({stats['combined']['scenario2_percentage']}%)

## Scenario 1 Statistics / 场景1统计

### Count by Complexity / 按复杂度统计
"""
        
        for complexity, count in stats['scenario1'].get('by_complexity', {}).items():
            summary += f"- {complexity}: {count}\n"
        
        summary += f"\n### Average Reasoning Steps / 平均推理步骤数\n"
        summary += f"- {stats['scenario1']['avg_reasoning_steps']} steps per Q&A\n"
        
        summary += f"\n## Scenario 2 Statistics / 场景2统计\n\n"
        summary += f"### Average Analysis Steps / 平均分析步骤数\n"
        summary += f"- {stats['scenario2']['avg_decision_points']} points per design\n"
        
        summary += "\n## Next Steps / 下一步\n\n"
        summary += "1. Review the training dataset JSONL file\n"
        summary += "2. Verify quality and diversity of generated data\n"
        summary += "3. Use for model fine-tuning\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info(f"Created review summary at {output_file}")
        return str(output_file)

    def process_all_outputs(self, batch_output_dir: str = "data/4.batch_output",
                           train_ratio: float = 0.8, val_ratio: float = 0.2,
                           random_seed: int = 42) -> Dict[str, Any]:
        """
        Complete pipeline: scan outputs, process by repo, create unified datasets
        完整流程：扫描输出，按仓库处理，创建统一数据集

        Args:
            batch_output_dir: Directory containing batch output files
            train_ratio: Ratio of training data
            val_ratio: Ratio of validation data
            random_seed: Random seed for shuffling

        Returns:
            Dictionary with all processing results
        """
        logger.info("Starting complete dataset compilation pipeline for Qwen...")

        # Step 1: Load source data for mapping
        self.load_source_data()

        # Step 2: Scan and load all batch outputs
        self.scan_and_load_batch_outputs(batch_output_dir)

        # Step 3: Process and export by repository
        repo_files = self.process_and_export_by_repo()

        # Step 4: Create unified train/val datasets
        unified_files = self.create_unified_dataset(train_ratio, val_ratio, random_seed)

        # Step 5: Generate statistics
        stats = self.generate_statistics()
        stats_file = self.export_statistics()

        # Step 6: Create review summary
        summary_file = self.create_review_summary()

        results = {
            "repo_files": repo_files,
            "unified_datasets": unified_files,
            "statistics": stats,
            "statistics_file": stats_file,
            "summary_file": summary_file,
            "processing_timestamp": datetime.now().isoformat()
        }

        logger.info("Dataset compilation pipeline completed successfully")
        return results


def main():
    """Command line interface / 命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description="Compile OpenAI batch outputs into training datasets")
    parser.add_argument("--batch-output-dir", "-i", default="data/4.batch_output",
                       help="Directory containing batch output JSONL files")
    parser.add_argument("--source-data-dir", "-s", default="data/2.reviewed_slices",
                       help="Directory containing original reviewed slices")
    parser.add_argument("--output-dir", "-o", default="data/5.final_output",
                       help="Output directory for final datasets")
    parser.add_argument("--train-ratio", "-tr", type=float, default=0.8,
                       help="Ratio of training data (0.0-1.0)")
    parser.add_argument("--val-ratio", "-vr", type=float, default=0.2,
                       help="Ratio of validation data (0.0-1.0)")
    parser.add_argument("--random-seed", "-rs", type=int, default=42,
                       help="Random seed for shuffling")

    args = parser.parse_args()

    # Validate ratios
    if abs(args.train_ratio + args.val_ratio - 1.0) > 0.001:
        print("Error: train_ratio + val_ratio must equal 1.0")
        return 1

    # Process all outputs
    compiler = DatasetCompiler(output_dir=args.output_dir, source_data_dir=args.source_data_dir)
    results = compiler.process_all_outputs(
        batch_output_dir=args.batch_output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        random_seed=args.random_seed
    )

    # Print results
    print("Dataset compilation complete!")
    print("\nRepository-specific files:")
    for repo, files in results["repo_files"].items():
        print(f"  {repo}:")
        for scenario, file_path in files.items():
            print(f"    {scenario}: {file_path}")

    print("Unified datasets:")
    print(f"  Train: {results['unified_datasets']['train']}")
    print(f"  Val: {results['unified_datasets']['val']}")

    print("Statistics:")
    print(f"  File: {results['statistics_file']}")
    print(f"  Summary: {results['summary_file']}")

    print(f"\nTotal processed: {results['statistics']['combined']['total_items']} items")
    print(f"Scenario 1: {results['statistics']['scenario1']['total_count']} items")
    print(f"Scenario 2: {results['statistics']['scenario2']['total_count']} items")
    print(f"Scenario 1 parse success rate: {results['statistics']['scenario1']['parse_success_rate']}%")
    print(f"Scenario 2 parse success rate: {results['statistics']['scenario2']['parse_success_rate']}%")
    print(f"Scenario 1 avg reasoning steps: {results['statistics']['scenario1']['avg_reasoning_steps']}")
    print(f"Scenario 2 avg decision points: {results['statistics']['scenario2']['avg_decision_points']}")
    print(f"Overall parse success rate: {results['statistics']['combined']['overall_parse_success_rate']}%")

    return 0


if __name__ == "__main__":
    exit(main())

# D:\Code\Python\python.exe src/pipeline/dataset_compiler.py --batch-output-dir ./data/4.batch_output --output-dir ./data/5.final_output --train-ratio 0.8 --val-ratio 0.2 --random-seed 42

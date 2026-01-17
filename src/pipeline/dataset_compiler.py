"""
Dataset Compiler - Stage 5 of the pipeline
数据集编译器 - 流水线第五阶段

This module compiles processed data into final training datasets with statistics.
该模块将处理后的数据编译成最终的训练数据集并提供统计信息。
"""

import json
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetCompiler:
    """
    Dataset Compiler for creating final training datasets
    创建最终训练数据集的编译器
    """
    
    def __init__(self, output_dir: str = "final_output"):
        """
        Initialize DatasetCompiler
        
        Args:
            output_dir: Directory to save final datasets
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.scenario1_data: List[Dict[str, Any]] = []
        self.scenario2_data: List[Dict[str, Any]] = []
    
    def load_scenario_data(self, scenario1_file: Optional[str] = None,
                          scenario2_file: Optional[str] = None) -> None:
        """
        Load processed scenario data from JSONL files
        从JSONL文件加载处理后的场景数据
        
        Args:
            scenario1_file: Path to Scenario 1 data file
            scenario2_file: Path to Scenario 2 data file
        """
        if scenario1_file:
            self.scenario1_data = self._load_jsonl(scenario1_file)
            logger.info(f"Loaded {len(self.scenario1_data)} Scenario 1 items")
        
        if scenario2_file:
            self.scenario2_data = self._load_jsonl(scenario2_file)
            logger.info(f"Loaded {len(self.scenario2_data)} Scenario 2 items")
    
    def _load_jsonl(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data from JSONL file / 从JSONL文件加载数据"""
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
    
    def generate_statistics(self) -> Dict[str, Any]:
        """
        Generate comprehensive statistics about the dataset
        生成数据集的综合统计信息
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "generated_at": datetime.now().isoformat(),
            "scenario1": {
                "total_count": len(self.scenario1_data),
                "by_complexity": self._count_by_field(self.scenario1_data, "complexity"),
                "by_repository": self._count_by_field(self.scenario1_data, "repository"),
                "avg_reasoning_steps": self._calculate_avg_reasoning_steps(self.scenario1_data)
            },
            "scenario2": {
                "total_count": len(self.scenario2_data),
                "by_architecture_style": self._count_by_nested_field(
                    self.scenario2_data, 
                    "design_solution", 
                    "architecture", 
                    "style"
                ),
                "by_repository": self._count_by_field(self.scenario2_data, "repository"),
                "avg_decision_points": self._calculate_avg_decision_points(self.scenario2_data)
            },
            "combined": {
                "total_items": len(self.scenario1_data) + len(self.scenario2_data),
                "scenario1_percentage": round(
                    len(self.scenario1_data) / max(1, len(self.scenario1_data) + len(self.scenario2_data)) * 100, 
                    2
                ),
                "scenario2_percentage": round(
                    len(self.scenario2_data) / max(1, len(self.scenario1_data) + len(self.scenario2_data)) * 100,
                    2
                )
            }
        }
        
        return stats
    
    def _count_by_field(self, data: List[Dict[str, Any]], field: str) -> Dict[str, int]:
        """Count occurrences by field / 按字段统计出现次数"""
        values = [item.get(field, "unknown") for item in data]
        return dict(Counter(values))
    
    def _count_by_nested_field(self, data: List[Dict[str, Any]], 
                               *fields: str) -> Dict[str, int]:
        """Count occurrences by nested field / 按嵌套字段统计出现次数"""
        values = []
        for item in data:
            current = item
            for field in fields:
                if isinstance(current, dict):
                    current = current.get(field)
                else:
                    current = None
                    break
            if current:
                values.append(current)
            else:
                values.append("unknown")
        return dict(Counter(values))
    
    def _calculate_avg_reasoning_steps(self, data: List[Dict[str, Any]]) -> float:
        """Calculate average number of reasoning steps / 计算平均推理步骤数"""
        if not data:
            return 0.0
        
        total_steps = 0
        count = 0
        
        for item in data:
            reasoning_trace = item.get("reasoning_trace", {})
            steps = reasoning_trace.get("steps", [])
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
            reasoning_trace = item.get("reasoning_trace", {})
            decision_points = reasoning_trace.get("decision_points", [])
            if isinstance(decision_points, list):
                total_points += len(decision_points)
                count += 1
        
        return round(total_points / max(1, count), 2)
    
    def shuffle_and_merge(self, seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Shuffle and merge scenario data
        随机打乱并合并场景数据
        
        Args:
            seed: Random seed for reproducibility
            
        Returns:
            Merged and shuffled dataset
        """
        # Combine all data
        combined = []
        
        # Add scenario1 data with type marker
        for item in self.scenario1_data:
            item_copy = item.copy()
            item_copy["training_scenario"] = "scenario1_qa"
            combined.append(item_copy)
        
        # Add scenario2 data with type marker
        for item in self.scenario2_data:
            item_copy = item.copy()
            item_copy["training_scenario"] = "scenario2_design"
            combined.append(item_copy)
        
        # Shuffle
        if seed is not None:
            random.seed(seed)
        random.shuffle(combined)
        
        logger.info(f"Shuffled and merged {len(combined)} items")
        return combined
    
    def export_training_dataset(self, output_file: Optional[str] = None,
                               shuffle: bool = True,
                               seed: Optional[int] = 42) -> str:
        """
        Export final training dataset to JSONL
        导出最终训练数据集到JSONL
        
        Args:
            output_file: Output file path
            shuffle: Whether to shuffle the data
            seed: Random seed for shuffling
            
        Returns:
            Path to exported file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"training_dataset_{timestamp}.jsonl"
        else:
            output_file = Path(output_file)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Get merged data
        if shuffle:
            dataset = self.shuffle_and_merge(seed=seed)
        else:
            dataset = self.scenario1_data + self.scenario2_data
        
        # Write JSONL
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in dataset:
                json_line = json.dumps(item, ensure_ascii=False)
                f.write(json_line + '\n')
        
        logger.info(f"Exported training dataset to {output_file}")
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
        summary += f"### Count by Architecture Style / 按架构风格统计\n"
        
        for style, count in stats['scenario2'].get('by_architecture_style', {}).items():
            summary += f"- {style}: {count}\n"
        
        summary += f"\n### Average Decision Points / 平均决策点数\n"
        summary += f"- {stats['scenario2']['avg_decision_points']} points per design\n"
        
        summary += "\n## Next Steps / 下一步\n\n"
        summary += "1. Review the training dataset JSONL file\n"
        summary += "2. Verify quality and diversity of generated data\n"
        summary += "3. Use for model fine-tuning\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info(f"Created review summary at {output_file}")
        return str(output_file)

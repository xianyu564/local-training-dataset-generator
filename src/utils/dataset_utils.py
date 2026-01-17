"""
Utility functions for dataset generation
数据集生成的实用函数
"""

import json
from pathlib import Path
from typing import List, Dict, Any


def validate_dataset(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate dataset quality and completeness
    验证数据集质量和完整性
    
    Args:
        dataset: List of dataset items
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "total_items": len(dataset),
        "valid_items": 0,
        "invalid_items": 0,
        "issues": []
    }
    
    required_fields = {
        "qa_pair": ["id", "type", "language", "question", "answer", "code_context", 
                    "business_rules", "reasoning_trace", "metadata"],
        "design_solution": ["id", "type", "language", "requirement", "design_solution",
                           "code_references", "reasoning_trace", "metadata"]
    }
    
    for idx, item in enumerate(dataset):
        item_type = item.get("type")
        
        if item_type not in required_fields:
            results["invalid_items"] += 1
            results["issues"].append(f"Item {idx}: Unknown type '{item_type}'")
            continue
        
        # Check required fields
        missing_fields = []
        for field in required_fields[item_type]:
            if field not in item:
                missing_fields.append(field)
        
        if missing_fields:
            results["invalid_items"] += 1
            results["issues"].append(f"Item {idx}: Missing fields {missing_fields}")
        else:
            results["valid_items"] += 1
    
    results["validity_rate"] = results["valid_items"] / results["total_items"] if results["total_items"] > 0 else 0
    
    return results


def calculate_diversity_score(dataset: List[Dict[str, Any]]) -> float:
    """
    Calculate diversity score of the dataset
    计算数据集的多样性分数
    
    Args:
        dataset: List of dataset items
        
    Returns:
        Diversity score between 0 and 1
    """
    if not dataset:
        return 0.0
    
    # Check complexity distribution
    complexities = [item.get("metadata", {}).get("complexity") for item in dataset]
    unique_complexities = len(set(c for c in complexities if c))
    
    # Check tag diversity
    all_tags = []
    for item in dataset:
        tags = item.get("metadata", {}).get("tags", [])
        all_tags.extend(tags)
    unique_tags = len(set(all_tags))
    
    # Check language coverage
    languages = [item.get("language") for item in dataset]
    unique_languages = len(set(l for l in languages if l))
    
    # Normalize scores
    complexity_score = min(unique_complexities / 3.0, 1.0)  # Max 3 levels
    tag_score = min(unique_tags / 10.0, 1.0)  # Expect at least 10 unique tags
    language_score = min(unique_languages / 2.0, 1.0)  # Max 2 languages
    
    # Weighted average
    diversity_score = (complexity_score * 0.3 + tag_score * 0.4 + language_score * 0.3)
    
    return diversity_score


def merge_datasets(*datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge multiple datasets
    合并多个数据集
    
    Args:
        *datasets: Variable number of dataset lists
        
    Returns:
        Merged dataset
    """
    merged = []
    seen_ids = set()
    
    for dataset in datasets:
        for item in dataset:
            item_id = item.get("id")
            if item_id and item_id not in seen_ids:
                merged.append(item)
                seen_ids.add(item_id)
    
    return merged


def filter_by_complexity(dataset: List[Dict[str, Any]], 
                        complexity: str) -> List[Dict[str, Any]]:
    """
    Filter dataset by complexity level
    按复杂度级别过滤数据集
    
    Args:
        dataset: List of dataset items
        complexity: Complexity level ("simple", "medium", "complex")
        
    Returns:
        Filtered dataset
    """
    return [
        item for item in dataset
        if item.get("metadata", {}).get("complexity") == complexity
    ]


def split_train_test(dataset: List[Dict[str, Any]], 
                     test_ratio: float = 0.2) -> tuple:
    """
    Split dataset into train and test sets
    将数据集分为训练集和测试集
    
    Args:
        dataset: List of dataset items
        test_ratio: Ratio of test set (0.0 to 1.0)
        
    Returns:
        Tuple of (train_set, test_set)
    """
    import random
    
    shuffled = dataset.copy()
    random.shuffle(shuffled)
    
    split_idx = int(len(shuffled) * (1 - test_ratio))
    train_set = shuffled[:split_idx]
    test_set = shuffled[split_idx:]
    
    return train_set, test_set


def export_to_jsonl(dataset: List[Dict[str, Any]], output_file: str) -> None:
    """
    Export dataset to JSONL format (one JSON object per line)
    导出数据集为JSONL格式（每行一个JSON对象）
    
    Args:
        dataset: List of dataset items
        output_file: Output file path
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def load_from_jsonl(input_file: str) -> List[Dict[str, Any]]:
    """
    Load dataset from JSONL format
    从JSONL格式加载数据集
    
    Args:
        input_file: Input file path
        
    Returns:
        List of dataset items
    """
    dataset = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                dataset.append(json.loads(line))
    return dataset


def generate_statistics_report(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate comprehensive statistics report
    生成综合统计报告
    
    Args:
        dataset: List of dataset items
        
    Returns:
        Dictionary with statistics
    """
    stats = {
        "total_items": len(dataset),
        "by_type": {},
        "by_language": {},
        "by_complexity": {},
        "diversity_score": calculate_diversity_score(dataset),
        "validation": validate_dataset(dataset)
    }
    
    # Count by type
    for item in dataset:
        item_type = item.get("type", "unknown")
        stats["by_type"][item_type] = stats["by_type"].get(item_type, 0) + 1
    
    # Count by language
    for item in dataset:
        lang = item.get("language", "unknown")
        stats["by_language"][lang] = stats["by_language"].get(lang, 0) + 1
    
    # Count by complexity
    for item in dataset:
        complexity = item.get("metadata", {}).get("complexity", "unknown")
        stats["by_complexity"][complexity] = stats["by_complexity"].get(complexity, 0) + 1
    
    return stats

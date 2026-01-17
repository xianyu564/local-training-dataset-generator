# -*- coding: utf-8 -*-
"""
Scenario Processor - Generate Batch Input JSONL from Reviewed Slices
场景处理器 - 从审核后的切片生成批处理输入JSONL

Converts data/2.reviewed_slices to data/3.batch_input JSONL files with trace requirements.
将 data/2.reviewed_slices 转换为 data/3.batch_input JSONL文件，包含推理轨迹需求。
"""

import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScenarioProcessor:
    """
    Process reviewed slices into batch input JSONL files
    将审核后的切片处理为批处理输入JSONL文件
    """

    def __init__(self, output_dir: str = "data/3.batch_input", config_path: str = "config.json"):
        """
        Initialize ScenarioProcessor

        Args:
            output_dir: Directory to save batch input JSONL files
            config_path: Path to configuration file for model settings
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load model configuration
        self.config = self._load_config(config_path)

        # Predefined requirements for scenario 2
        self.scenario2_requirements = [
            {
                "title": "增加微信支付功能",
                "description": "为电商系统添加微信支付支持，需要处理支付回调和退款",
                "constraints": ["必须复用现有的支付接口抽象", "支持微信小程序和H5"]
            },
            {
                "title": "实现用户行为分析",
                "description": "添加用户行为追踪和分析功能，包括点击流和转化率统计",
                "constraints": ["使用现有的事件系统", "数据存储到现有数据库"]
            },
            {
                "title": "添加缓存层",
                "description": "为频繁查询的接口添加Redis缓存，提高响应速度",
                "constraints": ["保持现有API接口不变", "支持缓存失效策略"]
            },
            {
                "title": "实现文件上传服务",
                "description": "添加安全的文件上传、存储和访问功能",
                "constraints": ["支持多种文件类型", "集成现有的权限系统"]
            },
            {
                "title": "添加消息通知系统",
                "description": "实现邮件、短信、站内信等多种通知方式",
                "constraints": ["使用异步队列处理", "支持模板化消息"]
            }
        ]

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration for model settings"""
        config_file = Path(config_path)

        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                full_config = json.load(f)

            # Handle nested config structure
            if "openai" in full_config:
                return full_config["openai"]
            else:
                return full_config
        else:
            # Default configuration
            return {
                "model": "gpt-5-nano-2025-08-07"
            }

    def process_reviewed_slices(self, reviewed_slices_dir: str = "data/2.reviewed_slices",
                               max_scenario1: int = 100000, max_scenario2: int = 100000) -> Dict[str, str]:
        """
        Process reviewed slices into batch input JSONL files with trace requirements
        将审核后的切片处理为包含推理轨迹需求的批处理输入JSONL文件

        Args:
            reviewed_slices_dir: Directory containing reviewed slice JSONL files
            max_scenario1: Maximum items for scenario 1 (functions)
            max_scenario2: Maximum items for scenario 2 (classes)

        Returns:
            Dictionary mapping scenario names to output file paths
        """
        reviewed_dir = Path(reviewed_slices_dir)
        if not reviewed_dir.exists():
            raise FileNotFoundError(f"Reviewed slices directory not found: {reviewed_dir}")

        # Collect all reviewed slices
        all_slices = []
        for jsonl_file in reviewed_dir.glob("*.jsonl"):
            logger.info(f"Loading reviewed slices from: {jsonl_file}")
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        all_slices.append(json.loads(line))

        logger.info(f"Total reviewed slices loaded: {len(all_slices)}")

        # Split by scenario: functions for scenario1, classes for scenario2
        scenario1_slices = [s for s in all_slices if s.get('type') == 'function'][:max_scenario1]
        scenario2_slices = [s for s in all_slices if s.get('type') == 'class'][:max_scenario2]

        logger.info(f"Scenario 1 slices (functions): {len(scenario1_slices)}")
        logger.info(f"Scenario 2 slices (classes): {len(scenario2_slices)}")

        results = {}

        # Generate scenario 1 JSONL (functions with full code)
        if scenario1_slices:
            scenario1_file = self._generate_scenario1_jsonl(scenario1_slices)
            results["scenario1"] = scenario1_file
            logger.info(f"Scenario 1 JSONL created: {scenario1_file}")

        # Generate scenario 2 JSONL (classes with architecture skeleton)
        if scenario2_slices:
            scenario2_file = self._generate_scenario2_jsonl(scenario2_slices)
            results["scenario2"] = scenario2_file
            logger.info(f"Scenario 2 JSONL created: {scenario2_file}")

        return results

    def _generate_scenario1_jsonl(self, slices: List[Dict[str, Any]]) -> str:
        """Generate JSONL for scenario 1 (functions with reasoning trace requirements)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"scenario1_batch_input_{timestamp}.jsonl"

        with open(output_file, 'w', encoding='utf-8') as f:
            for slice_data in slices:
                jsonl_item = self._create_scenario1_item(slice_data)
                f.write(json.dumps(jsonl_item, ensure_ascii=False) + '\n')

        logger.info(f"Generated {len(slices)} scenario 1 items")
        return str(output_file)

    def _generate_scenario2_jsonl(self, slices: List[Dict[str, Any]]) -> str:
        """Generate JSONL for scenario 2 (classes with design reasoning requirements)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"scenario2_batch_input_{timestamp}.jsonl"

        with open(output_file, 'w', encoding='utf-8') as f:
            for slice_data in slices:
                jsonl_item = self._create_scenario2_item(slice_data)
                f.write(json.dumps(jsonl_item, ensure_ascii=False) + '\n')

        logger.info(f"Generated {len(slices)} scenario 2 items")
        return str(output_file)

    def _create_scenario1_item(self, slice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create JSONL item for scenario 1 with reasoning trace requirement"""
        code_snippet = slice_data['code_snippet']
        file_path = slice_data['file_path']
        name = slice_data['name']
        context = slice_data.get('context', {})
        complexity = slice_data['complexity']

        # Build prompt requiring reasoning trace
        prompt = self._build_scenario1_prompt(code_snippet, file_path, name, context, complexity)

        return {
            "custom_id": f"scenario1_{slice_data['id']}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": self.config.get("model", "gpt-5-nano-2025-08-07"),
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a senior software architect creating training data. Generate detailed reasoning traces for code analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            }
        }

    def _create_scenario2_item(self, slice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create JSONL item for scenario 2 with design reasoning requirement"""
        # Select random requirement
        requirement = random.choice(self.scenario2_requirements)

        # Build architecture skeleton
        skeleton = self._build_architecture_skeleton(slice_data)

        # Build prompt requiring design reasoning
        prompt = self._build_scenario2_prompt(skeleton, requirement)

        return {
            "custom_id": f"scenario2_{slice_data['id']}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": self.config.get("model", "gpt-5-nano-2025-08-07"),
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a senior software architect creating training data. Generate detailed reasoning traces for system design."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        }

    def _build_scenario1_prompt(self, code_snippet: str, file_path: str, name: str,
                               context: Dict[str, Any], complexity: str) -> str:
        """Build prompt for scenario 1 requiring reasoning trace"""
        # Determine focus based on complexity
        if complexity == 'simple':
            focus = "这段代码的基本功能和工作原理"
        elif complexity == 'medium':
            focus = "这段代码的核心业务逻辑和设计思路"
        else:
            focus = "这段代码最复杂的部分及其优化空间"

        return f"""Analyze this Python function and generate a training sample with reasoning trace.

Function: {file_path}::{name}
Complexity: {complexity}
Docstring: {context.get('docstring', 'None')}

Code:
```python
{code_snippet}
```

Generate a JSON training sample:
{{
  "question": "A specific technical question about {focus}",
  "answer": "Detailed explanation of the code",
  "reasoning_trace": {{
    "steps": [
      {{
        "step_number": 1,
        "description": "Analysis step description",
        "code_reference": "Specific code element",
        "reasoning": "Why this step matters"
      }}
    ],
    "conclusion": "Final understanding"
  }},
  "business_rules": ["Extracted business rules"]
}}

Return only valid JSON."""

    def _build_architecture_skeleton(self, slice_data: Dict[str, Any]) -> str:
        """Build architecture skeleton from class data"""
        file_path = slice_data['file_path']
        name = slice_data['name']
        context = slice_data.get('context', {})

        skeleton = f"""Class: {name}
File: {file_path}
Docstring: {context.get('docstring', 'None')}
Base classes: {', '.join(context.get('base_classes', []))}

Methods:
"""

        for method in context.get('methods', []):
            if isinstance(method, dict):
                skeleton += f"- {method.get('name', 'unknown')}()\n"
            else:
                skeleton += f"- {method}()\n"

        return skeleton

    def _build_scenario2_prompt(self, skeleton: str, requirement: Dict[str, Any]) -> str:
        """Build prompt for scenario 2 requiring design reasoning"""
        return f"""Design a solution for this requirement using the existing class architecture.

Existing Architecture:
{skeleton}

Requirement:
Title: {requirement['title']}
Description: {requirement['description']}
Constraints: {', '.join(requirement['constraints'])}

Generate a JSON design solution:
{{
  "requirement_analysis": {{
    "title": "{requirement['title']}",
    "description": "{requirement['description']}",
    "constraints": {requirement['constraints']}
  }},
  "design_solution": {{
    "overview": "High-level design approach",
    "architecture": {{
      "components": ["New components to add"],
      "integration_points": ["Integration points"],
      "data_flow": "Data flow description"
    }},
    "implementation_plan": ["Implementation steps"]
  }},
  "reasoning_trace": {{
    "analysis_steps": [
      {{
        "step": 1,
        "existing_pattern_analysis": "How existing patterns inform design",
        "requirement_mapping": "How requirements map to architecture",
        "decision_factors": "Key decision factors"
      }}
    ],
    "design_rationale": "Why this design approach"
  }}
}}

Return only valid JSON."""


def main():
    """Command line interface / 命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate batch input JSONL from reviewed slices")
    parser.add_argument("--reviewed-dir", "-r", default="data/2.reviewed_slices",
                       help="Directory containing reviewed slice JSONL files")
    parser.add_argument("--output-dir", "-o", default="data/3.batch_input",
                       help="Output directory for batch input files")
    parser.add_argument("--max-scenario1", "-s1", type=int, default=100000,
                       help="Maximum items for scenario 1 (functions for QA)")
    parser.add_argument("--max-scenario2", "-s2", type=int, default=100000,
                       help="Maximum items for scenario 2 (classes for design)")

    args = parser.parse_args()

    # Process reviewed slices
    processor = ScenarioProcessor(output_dir=args.output_dir)
    results = processor.process_reviewed_slices(
        reviewed_slices_dir=args.reviewed_dir,
        max_scenario1=args.max_scenario1,
        max_scenario2=args.max_scenario2
    )

    # Print results
    print("Batch input JSONL generation complete!")
    for scenario, file_path in results.items():
        print(f"  {scenario}: {file_path}")
    print("\nNext: Use batch_submitter.py to submit to OpenAI")


if __name__ == "__main__":
    main()


# =============================================================================
# 调用示例 / Usage Examples
# =============================================================================

"""
# 1. 基本用法 - 从审核切片生成批处理输入JSONL / Basic Usage - Generate Batch Input JSONL
python src/pipeline/scenario_processor.py

# 2. 指定目录 - Specify directories
python src/pipeline/scenario_processor.py \
  --reviewed-dir data/2.reviewed_slices \
  --output-dir data/3.batch_input

# 3. 控制数据量 - Control data volume
python src/pipeline/scenario_processor.py \
  --max-scenario1 100000 \
  --max-scenario2 100000    

# 4. Python API 调用 / Python API Usage
from src.pipeline.scenario_processor import ScenarioProcessor

processor = ScenarioProcessor()
results = processor.process_reviewed_slices(
    reviewed_slices_dir="data/2.reviewed_slices",
    max_scenario1=50,
    max_scenario2=25
)
print("Generated JSONL files:", results)

# 输出文件 / Output files:
# data/3.batch_input/scenario1_batch_input_YYYYMMDD_HHMMSS.jsonl
# data/3.batch_input/scenario2_batch_input_YYYYMMDD_HHMMSS.jsonl
"""

# D:\Code\Python\python.exe  src/pipeline/scenario_processor.py --reviewed-dir ./data/2.reviewed_slices/repo_fastapi_light/ --output-dir ./data/3.batch_input/repo_fastapi_light/   
# D:\Code\Python\python.exe  src/pipeline/scenario_processor.py --reviewed-dir ./data/2.reviewed_slices/repo_ecommerce_medium/ --output-dir ./data/3.batch_input/repo_ecommerce_medium/   
# D:\Code\Python\python.exe  src/pipeline/scenario_processor.py --reviewed-dir ./data/2.reviewed_slices/repo_iot_special/ --output-dir ./data/3.batch_input/repo_iot_special/   

# =============================================================================
# 场景区分 / Scenario Differentiation
# =============================================================================

"""
场景1 (QA): 函数 + 推理轨迹需求
- 输入: 函数完整代码片段 + 上下文
- 让OpenAI生成: 技术问题 + 解答 + 推理步骤 + 业务规则

场景2 (Design): 类架构 + 设计需求
- 输入: 类结构骨架 + 随机业务需求
- 让OpenAI生成: 需求分析 + 设计方案 + 推理轨迹 + 实现计划
"""
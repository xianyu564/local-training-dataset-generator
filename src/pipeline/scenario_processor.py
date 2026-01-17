# -*- coding: utf-8 -*-
"""
Scenario Processor - Convert reviewed slices to batch input
场景处理器 - 将审核后的切片转换为批处理输入

Converts data/2.reviewed_slices to data/3.batch_input for scenarios 1 and 2.
将 data/2.reviewed_slices 转换为 data/3.batch_input，用于场景1和场景2。
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    """Represents a batch API request / 代表一个批处理API请求"""
    custom_id: str
    method: str
    url: str
    body: Dict[str, Any]


class ScenarioProcessor:
    """
    Process reviewed slices into batch input for scenarios 1 and 2
    将审核后的切片处理为场景1和场景2的批处理输入
    """

    def __init__(self, output_dir: str = "data/3.batch_input"):
        """
        Initialize ScenarioProcessor

        Args:
            output_dir: Directory to save batch input files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_reviewed_slices(self, reviewed_slices_dir: str = "data/2.reviewed_slices",
                               max_scenario1: int = 100, max_scenario2: int = 50) -> Dict[str, str]:
        """
        Process all reviewed slice files into batch input
        将所有审核后的切片文件处理为批处理输入

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

        # Split by scenario
        scenario1_slices = [s for s in all_slices if s.get('type') == 'function'][:max_scenario1]
        scenario2_slices = [s for s in all_slices if s.get('type') == 'class'][:max_scenario2]

        logger.info(f"Scenario 1 slices: {len(scenario1_slices)}")
        logger.info(f"Scenario 2 slices: {len(scenario2_slices)}")

        # Create batch requests
        results = {}

        if scenario1_slices:
            scenario1_requests = self._create_scenario1_requests(scenario1_slices)
            scenario1_file = self._export_batch_requests(scenario1_requests, "scenario1")
            results["scenario1"] = scenario1_file
            logger.info(f"Scenario 1 batch input created: {scenario1_file}")

        if scenario2_slices:
            scenario2_requests = self._create_scenario2_requests(scenario2_slices)
            scenario2_file = self._export_batch_requests(scenario2_requests, "scenario2")
            results["scenario2"] = scenario2_file
            logger.info(f"Scenario 2 batch input created: {scenario2_file}")

        return results

    def _create_scenario1_requests(self, slices: List[Dict[str, Any]]) -> List[BatchRequest]:
        """Create batch requests for Scenario 1 (Q&A with reasoning trace)"""
        requests = []

        for slice_data in slices:
            custom_id = f"scenario1_{slice_data['id']}"

            # Create prompt for Q&A generation with reasoning trace
            prompt = self._build_scenario1_prompt(slice_data)

            request = BatchRequest(
                custom_id=custom_id,
                method="POST",
                url="/v1/chat/completions",
                body={
                    "model": "gpt-4o-mini",  # Default model
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a senior software architect helping to create training data for code understanding. Generate question-answer pairs with detailed reasoning traces."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            requests.append(request)

        return requests

    def _create_scenario2_requests(self, slices: List[Dict[str, Any]]) -> List[BatchRequest]:
        """Create batch requests for Scenario 2 (Design solutions with reasoning)"""
        requests = []

        for slice_data in slices:
            custom_id = f"scenario2_{slice_data['id']}"

            # Create prompt for design solution generation
            prompt = self._build_scenario2_prompt(slice_data)

            request = BatchRequest(
                custom_id=custom_id,
                method="POST",
                url="/v1/chat/completions",
                body={
                    "model": "gpt-4o-mini",  # Default model
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a senior software architect helping to create training data for system design. Generate design solutions with detailed reasoning and decision traces."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            requests.append(request)

        return requests

    def _build_scenario1_prompt(self, slice_data: Dict[str, Any]) -> str:
        """Build prompt for Scenario 1 / 构建场景1的提示"""
        code_snippet = slice_data['code_snippet']
        file_path = slice_data['file_path']
        name = slice_data['name']
        context = slice_data.get('context', {})

        prompt = f"""Analyze the following code from {file_path}:

```python
{code_snippet}
```

Context:
- Name: {name}
- Type: {slice_data['type']}
- Complexity: {slice_data['complexity']}
- Docstring: {context.get('docstring', 'None')}

Please generate a Q&A pair about this code with the following structure in JSON format:

{{
  "question": "A technical question about this code (what it does, how it works, or why it's designed this way)",
  "answer": "A detailed answer explaining the code",
  "reasoning_trace": {{
    "steps": [
      {{
        "step_number": 1,
        "description": "What analysis was done",
        "code_reference": "Specific code element referenced",
        "reasoning": "Why this step is important"
      }}
    ],
    "conclusion": "Final understanding"
  }},
  "business_rules": ["List of business rules extracted from the code"]
}}

Generate the response in valid JSON format only."""

        return prompt

    def _build_scenario2_prompt(self, slice_data: Dict[str, Any]) -> str:
        """Build prompt for Scenario 2 / 构建场景2的提示"""
        code_snippet = slice_data['code_snippet']
        file_path = slice_data['file_path']
        name = slice_data['name']

        prompt = f"""Analyze the following code pattern from {file_path}:

```python
{code_snippet}
```

This code demonstrates a specific architectural pattern or design approach.

Please generate a design solution that someone might implement based on this pattern:

{{
  "requirement": {{
    "title": "A feature that could use this pattern",
    "description": "Detailed description",
    "constraints": ["List of constraints"]
  }},
  "design_solution": {{
    "overview": "High-level design approach",
    "architecture": {{
      "style": "Architecture style",
      "components": ["List of components"],
      "data_flow": "How data flows"
    }},
    "implementation_plan": ["Step-by-step implementation"]
  }},
  "reasoning_trace": {{
    "decision_points": [
      {{
        "decision": "Key decision made",
        "rationale": "Why this decision",
        "alternatives_considered": ["Other options"],
        "chosen_solution": "Why this was chosen"
      }}
    ]
  }}
}}

Generate the response in valid JSON format only."""

        return prompt

    def _export_batch_requests(self, requests: List[BatchRequest],
                              scenario: str, output_file: Optional[str] = None) -> str:
        """
        Export batch requests to JSONL file for batch API
        导出批处理请求到JSONL文件
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"{scenario}_batch_input_{timestamp}.jsonl"
        else:
            output_file = Path(output_file)

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            for req in requests:
                batch_item = {
                    "custom_id": req.custom_id,
                    "method": req.method,
                    "url": req.url,
                    "body": req.body
                }
                json_line = json.dumps(batch_item, ensure_ascii=False)
                f.write(json_line + '\n')

        logger.info(f"Exported {len(requests)} batch requests to {output_file}")
        return str(output_file)


def main():
    """Command line interface / 命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description="Convert reviewed slices to batch input")
    parser.add_argument("--reviewed-dir", "-r", default="data/2.reviewed_slices",
                       help="Directory containing reviewed slice JSONL files")
    parser.add_argument("--output-dir", "-o", default="data/3.batch_input",
                       help="Output directory for batch input files")
    parser.add_argument("--max-scenario1", "-s1", type=int, default=100,
                       help="Maximum items for scenario 1")
    parser.add_argument("--max-scenario2", "-s2", type=int, default=50,
                       help="Maximum items for scenario 2")

    args = parser.parse_args()

    # Process reviewed slices
    processor = ScenarioProcessor(output_dir=args.output_dir)
    results = processor.process_reviewed_slices(
        reviewed_slices_dir=args.reviewed_dir,
        max_scenario1=args.max_scenario1,
        max_scenario2=args.max_scenario2
    )

    # Print results
    print("Processing complete!")
    for scenario, file_path in results.items():
        print(f"  {scenario}: {file_path}")


if __name__ == "__main__":
    main()
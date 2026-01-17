"""
Batch Processor - Stage 3 of the pipeline
批处理器 - 流水线第三阶段

This module prepares code slices for GPT batch API processing and handles responses.
该模块为GPT批处理API准备代码切片并处理响应。
"""

import json
import logging
import yaml
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


class BatchProcessor:
    """
    Batch Processor for generating training data using LLM batch APIs
    使用LLM批处理API生成训练数据的批处理器
    """
    
    def __init__(self, config_path: str = "llm_config.yaml", 
                 output_dir: str = "batch_input"):
        """
        Initialize BatchProcessor
        
        Args:
            config_path: Path to LLM configuration file (gitignored)
            output_dir: Directory to save batch input files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load LLM configuration / 加载LLM配置"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.warning(f"Config file {config_path} not found. Using defaults.")
            return {
                "model": "gpt-4o-mini",  # Default to mini for cost efficiency
                "max_tokens": 2000,
                "temperature": 0.7
            }
        
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                return yaml.safe_load(f)
            else:
                return json.load(f)
    
    def create_scenario1_prompts(self, slices: List[Dict[str, Any]]) -> List[BatchRequest]:
        """
        Create prompts for Scenario 1 (Q&A with reasoning trace)
        为场景1创建提示（带推理轨迹的问答）
        
        Args:
            slices: List of code slice dictionaries
            
        Returns:
            List of BatchRequest objects
        """
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
                    "model": self.config.get("model", "gpt-4o-mini"),
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
                    "max_tokens": self.config.get("max_tokens", 2000),
                    "temperature": self.config.get("temperature", 0.7)
                }
            )
            requests.append(request)
        
        logger.info(f"Created {len(requests)} Scenario 1 batch requests")
        return requests
    
    def create_scenario2_prompts(self, slices: List[Dict[str, Any]]) -> List[BatchRequest]:
        """
        Create prompts for Scenario 2 (Design solutions with reasoning)
        为场景2创建提示（带推理的设计方案）
        
        Args:
            slices: List of code slice dictionaries
            
        Returns:
            List of BatchRequest objects
        """
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
                    "model": self.config.get("model", "gpt-4o-mini"),
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
                    "max_tokens": self.config.get("max_tokens", 2000),
                    "temperature": self.config.get("temperature", 0.7)
                }
            )
            requests.append(request)
        
        logger.info(f"Created {len(requests)} Scenario 2 batch requests")
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
    
    def export_batch_requests(self, requests: List[BatchRequest], 
                             scenario: str, output_file: Optional[str] = None) -> str:
        """
        Export batch requests to JSONL file for batch API
        导出批处理请求到JSONL文件
        
        Args:
            requests: List of BatchRequest objects
            scenario: "scenario1" or "scenario2"
            output_file: Optional output file path
            
        Returns:
            Path to exported file
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
    
    def parse_batch_responses(self, response_file: str, scenario: str) -> List[Dict[str, Any]]:
        """
        Parse batch API response file
        解析批处理API响应文件
        
        Args:
            response_file: Path to batch response JSONL file
            scenario: "scenario1" or "scenario2"
            
        Returns:
            List of parsed training data items
        """
        results = []
        
        with open(response_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                response = json.loads(line)
                custom_id = response.get('custom_id', '')
                
                # Extract the actual response content
                if 'response' in response:
                    response_body = response['response']
                    if 'body' in response_body:
                        choices = response_body['body'].get('choices', [])
                        if choices:
                            content = choices[0]['message']['content']
                            
                            # Parse JSON from content
                            try:
                                # Extract JSON from markdown code blocks if present
                                content_cleaned = content.strip()
                                if '```json' in content_cleaned:
                                    # Split by ```json and take the part after it
                                    parts = content_cleaned.split('```json')
                                    if len(parts) > 1:
                                        # Now split by ``` to get the content
                                        json_parts = parts[1].split('```')
                                        if json_parts:
                                            content_cleaned = json_parts[0].strip()
                                elif '```' in content_cleaned:
                                    # Generic code block
                                    parts = content_cleaned.split('```')
                                    if len(parts) >= 3:
                                        # Take the middle part (between first and last ```)
                                        content_cleaned = parts[1].strip()
                                
                                parsed_data = json.loads(content_cleaned)
                                parsed_data['id'] = custom_id
                                parsed_data['scenario'] = scenario
                                results.append(parsed_data)
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse JSON for {custom_id}: {e}")
        
        logger.info(f"Parsed {len(results)} responses from {response_file}")
        return results

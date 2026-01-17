"""
Data Models for Training Datasets
训练数据集的数据模型

Defines the structure for Q&A pairs and design solutions.
定义问答对和设计方案的结构。
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


@dataclass
class CodeContext:
    """Code context information / 代码上下文信息"""
    file_path: str
    code_snippet: str
    start_line: int
    end_line: int
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReasoningStep:
    """Single reasoning step / 单个推理步骤"""
    step_number: int
    description: str
    code_reference: str
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReasoningTrace:
    """Complete reasoning trace / 完整推理轨迹"""
    steps: List[ReasoningStep]
    conclusion: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "conclusion": self.conclusion
        }


@dataclass
class QAPair:
    """Question-Answer pair with context / 带上下文的问答对"""
    id: str
    question: str
    answer: str
    language: str  # "en" or "zh"
    code_context: CodeContext
    business_rules: List[str]
    reasoning_trace: ReasoningTrace
    metadata: Dict[str, Any]
    type: str = "qa_pair"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "language": self.language,
            "question": self.question,
            "answer": self.answer,
            "code_context": self.code_context.to_dict(),
            "business_rules": self.business_rules,
            "reasoning_trace": self.reasoning_trace.to_dict(),
            "metadata": self.metadata
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class Requirement:
    """Design requirement / 设计需求"""
    title: str
    description: str
    constraints: List[str]
    functional_requirements: List[str]
    non_functional_requirements: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Component:
    """Architecture component / 架构组件"""
    name: str
    responsibility: str
    interfaces: List[str]
    dependencies: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Architecture:
    """System architecture / 系统架构"""
    style: str
    components: List[Component]
    data_flow: str
    technology_stack: Dict[str, List[str]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "style": self.style,
            "components": [c.to_dict() for c in self.components],
            "data_flow": self.data_flow,
            "technology_stack": self.technology_stack
        }


@dataclass
class ImplementationPhase:
    """Implementation phase / 实施阶段"""
    phase: int
    description: str
    tasks: List[str]
    estimated_effort: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DesignSolutionContent:
    """Design solution content / 设计方案内容"""
    overview: str
    architecture: Architecture
    implementation_plan: List[ImplementationPhase]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overview": self.overview,
            "architecture": self.architecture.to_dict(),
            "implementation_plan": [p.to_dict() for p in self.implementation_plan]
        }


@dataclass
class CodeReference:
    """Reference to similar code / 相似代码引用"""
    file_path: str
    pattern_name: str
    code_snippet: str
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AlternativeOption:
    """Alternative design option / 备选设计选项"""
    option: str
    pros: List[str]
    cons: List[str]
    rejection_reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChosenSolution:
    """Chosen solution details / 选定方案详情"""
    description: str
    justification: str
    trade_offs: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionPoint:
    """Architectural decision point / 架构决策点"""
    decision: str
    rationale: str
    alternatives_considered: List[AlternativeOption]
    chosen_solution: ChosenSolution
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "rationale": self.rationale,
            "alternatives_considered": [a.to_dict() for a in self.alternatives_considered],
            "chosen_solution": self.chosen_solution.to_dict()
        }


@dataclass
class ArchitectureEvolution:
    """Architecture evolution stage / 架构演进阶段"""
    stage: str
    rationale: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DesignReasoningTrace:
    """Design reasoning trace / 设计推理轨迹"""
    decision_points: List[DecisionPoint]
    architecture_evolution: List[ArchitectureEvolution]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_points": [d.to_dict() for d in self.decision_points],
            "architecture_evolution": [e.to_dict() for e in self.architecture_evolution]
        }


@dataclass
class DesignSolution:
    """Complete design solution / 完整设计方案"""
    id: str
    requirement: Requirement
    design_solution: DesignSolutionContent
    code_references: Dict[str, List[CodeReference]]
    reasoning_trace: DesignReasoningTrace
    language: str  # "en" or "zh"
    metadata: Dict[str, Any]
    type: str = "design_solution"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "language": self.language,
            "requirement": self.requirement.to_dict(),
            "design_solution": self.design_solution.to_dict(),
            "code_references": {
                key: [ref.to_dict() for ref in refs]
                for key, refs in self.code_references.items()
            },
            "reasoning_trace": self.reasoning_trace.to_dict(),
            "metadata": self.metadata
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

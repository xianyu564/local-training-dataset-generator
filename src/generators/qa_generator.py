"""
Q&A Pair Generator for Scenario 1
场景1的问答对生成器

Generates question-answer pairs from code with reasoning traces.
从代码生成带推理轨迹的问答对。
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..dataset_generator.models import (
    QAPair, CodeContext, ReasoningTrace, ReasoningStep
)
from ..analyzers.code_analyzer import CodeAnalyzer, FunctionInfo, ClassInfo
import logging

logger = logging.getLogger(__name__)


class QAGenerator:
    """Generates Q&A pairs from code / 从代码生成问答对"""
    
    # Question templates for different types
    QUESTION_TEMPLATES = {
        "en": {
            "function_purpose": "What does the function `{name}` do?",
            "function_usage": "How do you use the function `{name}`?",
            "function_parameters": "What parameters does `{name}` accept?",
            "function_return": "What does `{name}` return?",
            "class_purpose": "What is the purpose of the `{name}` class?",
            "class_usage": "How do you use the `{name}` class?",
            "pattern": "What design pattern is used in `{name}`?",
            "business_logic": "What business logic is implemented in `{name}`?",
        },
        "zh": {
            "function_purpose": "函数 `{name}` 的作用是什么？",
            "function_usage": "如何使用函数 `{name}`？",
            "function_parameters": "`{name}` 接受哪些参数？",
            "function_return": "`{name}` 返回什么？",
            "class_purpose": "`{name}` 类的目的是什么？",
            "class_usage": "如何使用 `{name}` 类？",
            "pattern": "`{name}` 中使用了什么设计模式？",
            "business_logic": "`{name}` 中实现了什么业务逻辑？",
        }
    }
    
    def __init__(self, analyzer: CodeAnalyzer, repo_name: str):
        """Initialize generator with analyzer"""
        self.analyzer = analyzer
        self.repo_name = repo_name
        
    def generate_qa_pairs(self, max_pairs: int = 50, 
                          languages: List[str] = ["en", "zh"]) -> List[QAPair]:
        """Generate Q&A pairs / 生成问答对"""
        logger.info(f"Generating Q&A pairs for {self.repo_name}")
        
        qa_pairs = []
        
        # Generate from functions
        for func in self.analyzer.all_functions[:max_pairs // 2]:
            for lang in languages:
                qa = self._generate_function_qa(func, lang)
                if qa:
                    qa_pairs.append(qa)
                    if len(qa_pairs) >= max_pairs * len(languages):
                        return qa_pairs
        
        # Generate from classes
        for cls in self.analyzer.all_classes[:max_pairs // 4]:
            for lang in languages:
                qa = self._generate_class_qa(cls, lang)
                if qa:
                    qa_pairs.append(qa)
                    if len(qa_pairs) >= max_pairs * len(languages):
                        return qa_pairs
        
        logger.info(f"Generated {len(qa_pairs)} Q&A pairs")
        return qa_pairs
    
    def _generate_function_qa(self, func: FunctionInfo, language: str) -> Optional[QAPair]:
        """Generate Q&A for a function / 为函数生成问答"""
        try:
            # Choose question type based on available information
            if func.docstring:
                q_type = "function_purpose"
            elif func.parameters:
                q_type = "function_parameters"
            else:
                q_type = "function_usage"
            
            # Generate question
            question = self.QUESTION_TEMPLATES[language][q_type].format(name=func.name)
            
            # Generate answer
            answer = self._generate_function_answer(func, q_type, language)
            
            # Create code context
            code_snippet = '\n'.join(func.body_lines)
            code_context = CodeContext(
                file_path=func.file_path,
                code_snippet=code_snippet,
                start_line=func.start_line,
                end_line=func.end_line,
                function_name=func.name,
                class_name=None
            )
            
            # Extract business rules
            business_rules = self._extract_business_rules(func, language)
            
            # Generate reasoning trace
            reasoning_trace = self._generate_function_reasoning(func, q_type, language)
            
            # Create metadata
            metadata = {
                "repository": self.repo_name,
                "generated_at": datetime.now().isoformat(),
                "complexity": func.complexity,
                "tags": self._generate_tags(func)
            }
            
            return QAPair(
                id=str(uuid.uuid4()),
                question=question,
                answer=answer,
                language=language,
                code_context=code_context,
                business_rules=business_rules,
                reasoning_trace=reasoning_trace,
                metadata=metadata
            )
            
        except Exception as e:
            logger.warning(f"Failed to generate Q&A for function {func.name}: {e}")
            return None
    
    def _generate_function_answer(self, func: FunctionInfo, q_type: str, 
                                   language: str) -> str:
        """Generate answer for function question / 为函数问题生成答案"""
        if language == "en":
            if q_type == "function_purpose":
                base = f"The function `{func.name}` "
                if func.docstring:
                    # Use first line of docstring
                    first_line = func.docstring.split('\n')[0].strip()
                    base += first_line.lower() if first_line else "performs a specific operation."
                else:
                    base += "performs a specific operation based on its implementation."
                
                if func.parameters:
                    base += f" It accepts {len(func.parameters)} parameter(s): {', '.join(func.parameters)}."
                
                if func.returns:
                    base += f" It returns {func.returns}."
                
                return base
            
            elif q_type == "function_parameters":
                if func.parameters:
                    return (f"`{func.name}` accepts the following parameters: "
                           f"{', '.join(f'`{p}`' for p in func.parameters)}. "
                           f"These parameters are used in the function's logic to perform its operations.")
                return f"`{func.name}` does not accept any parameters."
            
            elif q_type == "function_usage":
                example = f"{func.name}("
                if func.parameters:
                    example += ", ".join(func.parameters)
                example += ")"
                return (f"To use `{func.name}`, call it with the required parameters. "
                       f"Example: `{example}`. {func.docstring.split('\n')[0] if func.docstring else ''}")
        
        else:  # zh
            if q_type == "function_purpose":
                base = f"函数 `{func.name}` "
                if func.docstring:
                    first_line = func.docstring.split('\n')[0].strip()
                    base += first_line if first_line else "执行特定操作。"
                else:
                    base += "根据其实现执行特定操作。"
                
                if func.parameters:
                    base += f" 它接受 {len(func.parameters)} 个参数：{', '.join(func.parameters)}。"
                
                if func.returns:
                    base += f" 它返回 {func.returns}。"
                
                return base
            
            elif q_type == "function_parameters":
                if func.parameters:
                    return (f"`{func.name}` 接受以下参数：{', '.join(f'`{p}`' for p in func.parameters)}。"
                           f"这些参数在函数逻辑中用于执行操作。")
                return f"`{func.name}` 不接受任何参数。"
            
            elif q_type == "function_usage":
                example = f"{func.name}("
                if func.parameters:
                    example += ", ".join(func.parameters)
                example += ")"
                return (f"要使用 `{func.name}`，使用所需参数调用它。"
                       f"示例：`{example}`。{func.docstring.split('\n')[0] if func.docstring else ''}")
        
        return "No specific answer available."
    
    def _extract_business_rules(self, func: FunctionInfo, language: str) -> List[str]:
        """Extract business rules from function / 从函数提取业务规则"""
        rules = []
        
        # Check for validation patterns
        code = '\n'.join(func.body_lines).lower()
        
        if 'if' in code and ('validate' in code or 'check' in code):
            if language == "en":
                rules.append("Includes validation logic to ensure data integrity")
            else:
                rules.append("包含验证逻辑以确保数据完整性")
        
        if 'raise' in code or 'except' in code:
            if language == "en":
                rules.append("Implements error handling for exceptional cases")
            else:
                rules.append("为异常情况实现错误处理")
        
        if not rules:
            if language == "en":
                rules.append("Follows standard implementation practices")
            else:
                rules.append("遵循标准实现实践")
        
        return rules
    
    def _generate_function_reasoning(self, func: FunctionInfo, q_type: str,
                                     language: str) -> ReasoningTrace:
        """Generate reasoning trace for function / 为函数生成推理轨迹"""
        steps = []
        
        if language == "en":
            # Step 1: Identify function signature
            steps.append(ReasoningStep(
                step_number=1,
                description="Analyze function signature",
                code_reference=f"def {func.name}({', '.join(func.parameters)})",
                reasoning=f"The function is named `{func.name}` and accepts {len(func.parameters)} parameter(s), "
                         f"indicating its input requirements."
            ))
            
            # Step 2: Examine documentation
            if func.docstring:
                steps.append(ReasoningStep(
                    step_number=2,
                    description="Review function documentation",
                    code_reference="docstring",
                    reasoning=f"The docstring provides: '{func.docstring.split('\n')[0]}', "
                             f"which explains the function's purpose."
                ))
            
            # Step 3: Analyze implementation
            steps.append(ReasoningStep(
                step_number=len(steps) + 1,
                description="Examine implementation details",
                code_reference=f"lines {func.start_line}-{func.end_line}",
                reasoning=f"The function has {func.complexity} complexity with "
                         f"{func.end_line - func.start_line + 1} lines of code, "
                         f"implementing the described functionality."
            ))
            
            conclusion = (f"Based on the signature, documentation, and implementation, "
                        f"`{func.name}` is designed to {func.docstring.split('\n')[0].lower() if func.docstring else 'perform its designated operation'}.")
        
        else:  # zh
            steps.append(ReasoningStep(
                step_number=1,
                description="分析函数签名",
                code_reference=f"def {func.name}({', '.join(func.parameters)})",
                reasoning=f"函数名为 `{func.name}`，接受 {len(func.parameters)} 个参数，"
                         f"表明其输入要求。"
            ))
            
            if func.docstring:
                steps.append(ReasoningStep(
                    step_number=2,
                    description="查看函数文档",
                    code_reference="docstring",
                    reasoning=f"文档字符串说明：'{func.docstring.split('\n')[0]}'，"
                             f"解释了函数的目的。"
                ))
            
            steps.append(ReasoningStep(
                step_number=len(steps) + 1,
                description="检查实现细节",
                code_reference=f"第 {func.start_line}-{func.end_line} 行",
                reasoning=f"函数具有 {func.complexity} 复杂度，共 "
                         f"{func.end_line - func.start_line + 1} 行代码，"
                         f"实现了所述功能。"
            ))
            
            conclusion = (f"根据签名、文档和实现，`{func.name}` 旨在"
                        f"{func.docstring.split('\n')[0] if func.docstring else '执行其指定操作'}。")
        
        return ReasoningTrace(steps=steps, conclusion=conclusion)
    
    def _generate_class_qa(self, cls: ClassInfo, language: str) -> Optional[QAPair]:
        """Generate Q&A for a class / 为类生成问答"""
        try:
            q_type = "class_purpose"
            question = self.QUESTION_TEMPLATES[language][q_type].format(name=cls.name)
            
            # Generate answer
            if language == "en":
                answer = f"The `{cls.name}` class "
                if cls.docstring:
                    answer += cls.docstring.split('\n')[0].lower()
                else:
                    answer += "provides functionality through its methods. "
                
                if cls.base_classes:
                    answer += f" It inherits from {', '.join(cls.base_classes)}."
                
                if cls.methods:
                    answer += f" It contains {len(cls.methods)} method(s) including {', '.join([m.name for m in cls.methods[:3]])}."
            else:
                answer = f"`{cls.name}` 类"
                if cls.docstring:
                    answer += cls.docstring.split('\n')[0]
                else:
                    answer += "通过其方法提供功能。"
                
                if cls.base_classes:
                    answer += f" 它继承自 {', '.join(cls.base_classes)}。"
                
                if cls.methods:
                    answer += f" 它包含 {len(cls.methods)} 个方法，包括 {', '.join([m.name for m in cls.methods[:3]])}。"
            
            # Get code snippet (class definition)
            code_snippet = self.analyzer.get_code_snippet(
                cls.file_path, cls.start_line, 
                min(cls.start_line + 20, cls.end_line)  # Limit to 20 lines
            )
            
            code_context = CodeContext(
                file_path=cls.file_path,
                code_snippet=code_snippet,
                start_line=cls.start_line,
                end_line=cls.end_line,
                function_name=None,
                class_name=cls.name
            )
            
            # Business rules
            business_rules = []
            if language == "en":
                business_rules.append("Encapsulates related functionality using OOP principles")
                if cls.base_classes:
                    business_rules.append("Uses inheritance to extend base functionality")
            else:
                business_rules.append("使用面向对象原则封装相关功能")
                if cls.base_classes:
                    business_rules.append("使用继承来扩展基础功能")
            
            # Reasoning trace
            reasoning_trace = self._generate_class_reasoning(cls, language)
            
            metadata = {
                "repository": self.repo_name,
                "generated_at": datetime.now().isoformat(),
                "complexity": "medium" if len(cls.methods) > 5 else "simple",
                "tags": ["class", "oop"] + ([f"inherits-{bc}" for bc in cls.base_classes])
            }
            
            return QAPair(
                id=str(uuid.uuid4()),
                question=question,
                answer=answer,
                language=language,
                code_context=code_context,
                business_rules=business_rules,
                reasoning_trace=reasoning_trace,
                metadata=metadata
            )
            
        except Exception as e:
            logger.warning(f"Failed to generate Q&A for class {cls.name}: {e}")
            return None
    
    def _generate_class_reasoning(self, cls: ClassInfo, language: str) -> ReasoningTrace:
        """Generate reasoning trace for class / 为类生成推理轨迹"""
        steps = []
        
        if language == "en":
            steps.append(ReasoningStep(
                step_number=1,
                description="Identify class structure",
                code_reference=f"class {cls.name}",
                reasoning=f"The class `{cls.name}` is defined with {len(cls.methods)} methods."
            ))
            
            if cls.base_classes:
                steps.append(ReasoningStep(
                    step_number=2,
                    description="Analyze inheritance",
                    code_reference=f"inherits from {', '.join(cls.base_classes)}",
                    reasoning="The class extends base classes to reuse and specialize functionality."
                ))
            
            conclusion = f"`{cls.name}` is a well-structured class that encapsulates related operations."
        else:
            steps.append(ReasoningStep(
                step_number=1,
                description="识别类结构",
                code_reference=f"class {cls.name}",
                reasoning=f"类 `{cls.name}` 定义了 {len(cls.methods)} 个方法。"
            ))
            
            if cls.base_classes:
                steps.append(ReasoningStep(
                    step_number=2,
                    description="分析继承",
                    code_reference=f"继承自 {', '.join(cls.base_classes)}",
                    reasoning="该类扩展基类以重用和专门化功能。"
                ))
            
            conclusion = f"`{cls.name}` 是一个结构良好的类，封装了相关操作。"
        
        return ReasoningTrace(steps=steps, conclusion=conclusion)
    
    def _generate_tags(self, func: FunctionInfo) -> List[str]:
        """Generate tags for function / 为函数生成标签"""
        tags = [func.complexity]
        
        if func.decorators:
            tags.extend([f"decorator-{d}" for d in func.decorators])
        
        code = '\n'.join(func.body_lines).lower()
        if 'async' in code or 'await' in code:
            tags.append('async')
        if 'class' in code:
            tags.append('oop')
        if 'return' in code:
            tags.append('returns-value')
        
        return tags

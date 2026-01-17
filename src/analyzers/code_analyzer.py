"""
Code Repository Analyzer
代码仓库分析器

Analyzes code repositories to extract structure and patterns.
分析代码仓库以提取结构和模式。
"""

import os
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from git import Repo
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """Function information / 函数信息"""
    name: str
    file_path: str
    start_line: int
    end_line: int
    docstring: Optional[str]
    parameters: List[str]
    returns: Optional[str]
    decorators: List[str]
    complexity: str  # "simple", "medium", "complex"
    body_lines: List[str]
    
    
@dataclass
class ClassInfo:
    """Class information / 类信息"""
    name: str
    file_path: str
    start_line: int
    end_line: int
    docstring: Optional[str]
    methods: List[FunctionInfo]
    base_classes: List[str]
    decorators: List[str]


@dataclass
class ModuleInfo:
    """Module information / 模块信息"""
    name: str
    file_path: str
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[str]
    docstring: Optional[str]


class CodeAnalyzer:
    """Analyzes Python code repositories / 分析Python代码仓库"""
    
    def __init__(self, repo_path: str):
        """Initialize analyzer with repository path"""
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        self.modules: List[ModuleInfo] = []
        self.all_functions: List[FunctionInfo] = []
        self.all_classes: List[ClassInfo] = []
        
    def analyze(self, max_files: Optional[int] = None) -> None:
        """Analyze the repository / 分析仓库"""
        logger.info(f"Starting analysis of {self.repo_path}")
        
        python_files = list(self.repo_path.rglob("*.py"))
        
        # Filter out test files and common excluded directories
        python_files = [
            f for f in python_files 
            if not any(part.startswith('.') or part in ['tests', 'test', '__pycache__', 'venv', 'env'] 
                      for part in f.parts)
        ]
        
        if max_files:
            python_files = python_files[:max_files]
        
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        for file_path in python_files:
            try:
                module_info = self._analyze_file(file_path)
                if module_info:
                    self.modules.append(module_info)
                    self.all_functions.extend(module_info.functions)
                    self.all_classes.extend(module_info.classes)
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        logger.info(f"Analysis complete: {len(self.modules)} modules, "
                   f"{len(self.all_functions)} functions, {len(self.all_classes)} classes")
    
    def _analyze_file(self, file_path: Path) -> Optional[ModuleInfo]:
        """Analyze a single Python file / 分析单个Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract module docstring
            docstring = ast.get_docstring(tree)
            
            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # Extract functions
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip nested functions (they'll be part of parent)
                    if self._is_top_level_function(node, tree):
                        func_info = self._extract_function_info(node, file_path, content)
                        if func_info:
                            functions.append(func_info)
            
            # Extract classes
            classes = []
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_info = self._extract_class_info(node, file_path, content)
                    if class_info:
                        classes.append(class_info)
            
            module_name = file_path.stem
            return ModuleInfo(
                name=module_name,
                file_path=str(file_path.relative_to(self.repo_path)),
                functions=functions,
                classes=classes,
                imports=imports,
                docstring=docstring
            )
            
        except SyntaxError:
            logger.warning(f"Syntax error in {file_path}")
            return None
    
    def _is_top_level_function(self, func_node: ast.FunctionDef, tree: ast.AST) -> bool:
        """Check if function is at module level / 检查函数是否在模块级别"""
        return func_node in tree.body
    
    def _extract_function_info(self, node: ast.FunctionDef, file_path: Path, 
                               content: str) -> Optional[FunctionInfo]:
        """Extract information from a function node / 从函数节点提取信息"""
        try:
            lines = content.split('\n')
            body_lines = lines[node.lineno - 1:node.end_lineno]
            
            # Get parameters
            parameters = [arg.arg for arg in node.args.args]
            
            # Get decorators
            decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
            
            # Get docstring
            docstring = ast.get_docstring(node)
            
            # Determine complexity based on lines and nesting
            complexity = self._calculate_complexity(node, body_lines)
            
            # Get return annotation
            returns = ast.unparse(node.returns) if node.returns else None
            
            return FunctionInfo(
                name=node.name,
                file_path=str(file_path.relative_to(self.repo_path)),
                start_line=node.lineno,
                end_line=node.end_lineno if node.end_lineno is not None else node.lineno,
                docstring=docstring,
                parameters=parameters,
                returns=returns,
                decorators=decorators,
                complexity=complexity,
                body_lines=body_lines
            )
        except Exception as e:
            logger.debug(f"Failed to extract function info: {e}")
            return None
    
    def _extract_class_info(self, node: ast.ClassDef, file_path: Path, 
                            content: str) -> Optional[ClassInfo]:
        """Extract information from a class node / 从类节点提取信息"""
        try:
            # Get base classes
            base_classes = [self._get_base_name(base) for base in node.bases]
            
            # Get decorators
            decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
            
            # Get docstring
            docstring = ast.get_docstring(node)
            
            # Get methods
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_info = self._extract_function_info(item, file_path, content)
                    if method_info:
                        methods.append(method_info)
            
            return ClassInfo(
                name=node.name,
                file_path=str(file_path.relative_to(self.repo_path)),
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                docstring=docstring,
                methods=methods,
                base_classes=base_classes,
                decorators=decorators
            )
        except Exception as e:
            logger.debug(f"Failed to extract class info: {e}")
            return None
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Get decorator name / 获取装饰器名称"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            return ast.unparse(decorator.func)
        return ast.unparse(decorator)
    
    def _get_base_name(self, base: ast.expr) -> str:
        """Get base class name / 获取基类名称"""
        if isinstance(base, ast.Name):
            return base.id
        return ast.unparse(base)
    
    def _calculate_complexity(self, node: ast.FunctionDef, body_lines: List[str]) -> str:
        """Calculate function complexity / 计算函数复杂度"""
        line_count = len(body_lines)
        
        # Count control flow statements
        control_flow_count = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                control_flow_count += 1
        
        if line_count <= 10 and control_flow_count <= 2:
            return "simple"
        elif line_count <= 30 and control_flow_count <= 5:
            return "medium"
        else:
            return "complex"
    
    def get_functions_by_complexity(self, complexity: str) -> List[FunctionInfo]:
        """Get functions filtered by complexity / 按复杂度获取函数"""
        return [f for f in self.all_functions if f.complexity == complexity]
    
    def get_code_snippet(self, file_path: str, start_line: int, end_line: int) -> str:
        """Get code snippet from file / 从文件获取代码片段"""
        full_path = self.repo_path / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return ''.join(lines[start_line - 1:end_line])
        except Exception as e:
            logger.error(f"Failed to get code snippet: {e}")
            return ""


class RepositoryCloner:
    """Clones and manages Git repositories / 克隆和管理Git仓库"""
    
    @staticmethod
    def clone(repo_url: str, target_path: str) -> str:
        """Clone a repository / 克隆仓库"""
        logger.info(f"Cloning repository from {repo_url}")
        
        target = Path(target_path)
        if target.exists():
            logger.info(f"Repository already exists at {target_path}")
            return str(target)
        
        try:
            Repo.clone_from(repo_url, target_path)
            logger.info(f"Successfully cloned to {target_path}")
            return str(target)
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise
    
    @staticmethod
    def get_repo_info(repo_path: str) -> Dict[str, Any]:
        """Get repository information / 获取仓库信息"""
        try:
            repo = Repo(repo_path)
            return {
                "remote_url": repo.remotes.origin.url if repo.remotes else None,
                "current_branch": repo.active_branch.name,
                "last_commit": repo.head.commit.hexsha[:7],
                "last_commit_date": repo.head.commit.committed_datetime.isoformat()
            }
        except Exception as e:
            logger.warning(f"Failed to get repo info: {e}")
            return {}

# -*- coding: utf-8 -*-
"""
Code Slicer - Standalone Repository Code Slicer
代码切片工具 - 独立仓库代码切片器

Slices Python code repositories into manageable segments.
将Python代码仓库切片成可管理的片段。
"""

import json
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class CodeSlice:
    """Represents a code slice / 代表一个代码片段"""
    id: str
    type: str  # "function", "class"
    repository: str
    file_path: str
    name: str
    start_line: int
    end_line: int
    code_snippet: str
    complexity: str
    context: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSONL export"""
        return asdict(self)


class SimpleCodeAnalyzer:
    """Simple code analyzer for Python files / Python文件简单代码分析器"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.all_functions = []
        self.all_classes = []

    def analyze(self, max_files: Optional[int] = None):
        """Analyze Python files in repository / 分析仓库中的Python文件"""
        python_files = list(self.repo_path.rglob("*.py"))
        if max_files:
            python_files = python_files[:max_files]

        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
            self._analyze_file(file_path)

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped / 检查是否应该跳过文件"""
        skip_patterns = [
            "__pycache__", "venv", "env", ".git", "node_modules",
            "test", "tests", "migrations", "build", "dist"
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file / 分析单个Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            relative_path = file_path.relative_to(self.repo_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef):
                    self._extract_function(node, content, str(relative_path))
                elif isinstance(node, ast.ClassDef):
                    self._extract_class(node, content, str(relative_path))

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def _extract_function(self, node: ast.FunctionDef, content: str, file_path: str):
        """Extract function information / 提取函数信息"""
        lines = content.split('\n')
        start_line = node.lineno - 1
        end_line = getattr(node, 'end_lineno', start_line + 10) - 1

        # Calculate complexity (simple heuristic)
        complexity = self._calculate_complexity(node)

        func_info = {
            'name': node.name,
            'file_path': file_path,
            'start_line': start_line + 1,
            'end_line': end_line + 1,
            'complexity': complexity,
            'docstring': ast.get_docstring(node) or "",
            'parameters': [arg.arg for arg in node.args.args],
            'returns': self._extract_return_annotation(node),
            'decorators': [getattr(dec, 'id', str(dec)) for dec in node.decorator_list]
        }
        self.all_functions.append(type('FunctionInfo', (), func_info)())

    def _extract_class(self, node: ast.ClassDef, content: str, file_path: str):
        """Extract class information / 提取类信息"""
        lines = content.split('\n')
        start_line = node.lineno - 1
        end_line = getattr(node, 'end_lineno', start_line + 20) - 1

        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append({'name': item.name})

        class_info = {
            'name': node.name,
            'file_path': file_path,
            'start_line': start_line + 1,
            'end_line': end_line + 1,
            'docstring': ast.get_docstring(node) or "",
            'base_classes': [getattr(base, 'id', str(base)) for base in node.bases],
            'methods': methods,
            'decorators': [getattr(dec, 'id', str(dec)) for dec in node.decorator_list]
        }
        self.all_classes.append(type('ClassInfo', (), class_info)())

    def _calculate_complexity(self, node: ast.FunctionDef) -> str:
        """Calculate function complexity / 计算函数复杂度"""
        complexity_score = 1  # base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                complexity_score += 1
            elif isinstance(child, ast.BoolOp):
                complexity_score += len(child.values) - 1

        if complexity_score <= 3:
            return "simple"
        elif complexity_score <= 7:
            return "medium"
        else:
            return "complex"

    def _extract_return_annotation(self, node: ast.FunctionDef) -> str:
        """Extract return type annotation / 提取返回类型注解"""
        if node.returns:
            return getattr(node.returns, 'id', str(node.returns))
        return ""

    def get_code_snippet(self, file_path: str, start_line: int, end_line: int) -> str:
        """Get code snippet from file / 从文件中获取代码片段"""
        full_path = self.repo_path / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return ''.join(lines[start_line-1:end_line])
        except Exception:
            return ""


class CodeSlicer:
    """Standalone Code Slicer / 独立代码切片器"""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else None
        self.slices: List[CodeSlice] = []

    def slice_repository(self, repo_path: str, repo_name: str = None,
                        max_files: Optional[int] = None) -> List[CodeSlice]:
        """Slice repository into code segments / 将仓库切片成代码片段"""
        repo_path = Path(repo_path)
        if not repo_name:
            repo_name = repo_path.name

        print(f"Slicing repository: {repo_name}")

        # Analyze repository
        analyzer = SimpleCodeAnalyzer(repo_path)
        analyzer.analyze(max_files=max_files)

        slices = []
        slice_counter = 0

        # Extract function slices
        for func in analyzer.all_functions:
            slice_id = f"{repo_name}_{slice_counter:05d}_func"
            slice_counter += 1

            code_snippet = analyzer.get_code_snippet(
                func.file_path, func.start_line, func.end_line
            )

            slice_obj = CodeSlice(
                id=slice_id,
                type="function",
                repository=repo_name,
                file_path=func.file_path,
                name=func.name,
                start_line=func.start_line,
                end_line=func.end_line,
                code_snippet=code_snippet,
                complexity=func.complexity,
                context={
                    "docstring": func.docstring,
                    "parameters": func.parameters,
                    "returns": func.returns,
                    "decorators": func.decorators
                },
                metadata={
                    "sliced_at": datetime.now().isoformat(),
                    "analyzer_version": "1.0"
                }
            )
            slices.append(slice_obj)

        # Extract class slices
        for cls in analyzer.all_classes:
            slice_id = f"{repo_name}_{slice_counter:05d}_class"
            slice_counter += 1

            code_snippet = analyzer.get_code_snippet(
                cls.file_path, cls.start_line, cls.end_line
            )

            slice_obj = CodeSlice(
                id=slice_id,
                type="class",
                repository=repo_name,
                file_path=cls.file_path,
                name=cls.name,
                start_line=cls.start_line,
                end_line=cls.end_line,
                code_snippet=code_snippet,
                complexity="medium",
                context={
                    "docstring": cls.docstring,
                    "base_classes": cls.base_classes,
                    "methods": [m['name'] for m in cls.methods],
                    "decorators": cls.decorators
                },
                metadata={
                    "sliced_at": datetime.now().isoformat(),
                    "analyzer_version": "1.0"
                }
            )
            slices.append(slice_obj)

        self.slices.extend(slices)
        print(f"Sliced {len(slices)} code segments from {repo_name}")

        return slices

    def export_slices(self, output_file: Optional[str] = None) -> str:
        """Export slices to JSONL file / 导出切片到JSONL文件"""
        if not output_file and self.output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"code_slices_{timestamp}.jsonl"
        elif not output_file:
            output_file = Path("code_slices.jsonl")

        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            for slice_obj in self.slices:
                json_line = json.dumps(slice_obj.to_dict(), ensure_ascii=False)
                f.write(json_line + '\n')

        print(f"Exported {len(self.slices)} slices to {output_file}")
        return str(output_file)


def main():
    """Command line interface / 命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description="Slice Python code repositories")
    parser.add_argument("repo_path", help="Path to repository to slice")
    parser.add_argument("--output-dir", "-o", help="Output directory for slices")
    parser.add_argument("--max-files", "-m", type=int, help="Maximum files to process")
    parser.add_argument("--repo-name", "-n", help="Repository name (default: directory name)")

    args = parser.parse_args()

    # Determine output directory
    repo_path = Path(args.repo_path)
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        # Default: data/1.slices/{repo_name}
        repo_name = args.repo_name or repo_path.name
        output_dir = Path("data") / "1.slices" / repo_name

    # Slice repository
    slicer = CodeSlicer()
    slicer.slice_repository(
        repo_path=str(repo_path),
        repo_name=args.repo_name,
        max_files=args.max_files
    )

    # Export slices
    output_file = slicer.export_slices(output_file=output_dir / "code_slices.jsonl")
    print(f"Slicing complete! Output: {output_file}")


if __name__ == "__main__":
    main()
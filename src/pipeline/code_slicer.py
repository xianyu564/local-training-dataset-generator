"""
Code Slicer - Stage 1 of the pipeline
代码切片工具 - 流水线第一阶段

This module slices code repositories into manageable segments for review and processing.
该模块将代码仓库切片成可管理的片段，供审核和处理。
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from ..analyzers.code_analyzer import CodeAnalyzer, FunctionInfo, ClassInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CodeSlice:
    """Represents a code slice / 代表一个代码片段"""
    id: str
    type: str  # "function", "class", "method"
    repository: str
    file_path: str
    name: str
    start_line: int
    end_line: int
    code_snippet: str
    complexity: str
    context: Dict[str, Any]  # Additional context like imports, docstring, etc.
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSONL export"""
        return asdict(self)


class CodeSlicer:
    """
    Code Slicer for extracting code segments from repositories
    从仓库中提取代码片段的切片工具
    """
    
    def __init__(self, output_dir: str = "slices"):
        """
        Initialize CodeSlicer
        
        Args:
            output_dir: Directory to save sliced code segments
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.slices: List[CodeSlice] = []
        
    def slice_repository(self, repo_path: str, repo_name: str, 
                        max_files: Optional[int] = None) -> List[CodeSlice]:
        """
        Slice a repository into code segments
        将仓库切片成代码片段
        
        Args:
            repo_path: Path to the repository
            repo_name: Name of the repository (e.g., "owner/repo")
            max_files: Maximum number of files to process
            
        Returns:
            List of CodeSlice objects
        """
        logger.info(f"Slicing repository: {repo_name} from {repo_path}")
        
        # Analyze repository
        analyzer = CodeAnalyzer(repo_path)
        analyzer.analyze(max_files=max_files)
        
        slices = []
        slice_counter = 0
        
        # Extract function slices
        for func in analyzer.all_functions:
            slice_id = f"{repo_name.replace('/', '_')}_{slice_counter:05d}_func"
            slice_counter += 1
            
            code_snippet = analyzer.get_code_snippet(
                func.file_path, 
                func.start_line, 
                func.end_line
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
            slice_id = f"{repo_name.replace('/', '_')}_{slice_counter:05d}_class"
            slice_counter += 1
            
            code_snippet = analyzer.get_code_snippet(
                cls.file_path,
                cls.start_line,
                cls.end_line
            )
            
            # Extract method info
            method_names = [m.name for m in cls.methods]
            
            slice_obj = CodeSlice(
                id=slice_id,
                type="class",
                repository=repo_name,
                file_path=cls.file_path,
                name=cls.name,
                start_line=cls.start_line,
                end_line=cls.end_line,
                code_snippet=code_snippet,
                complexity="medium",  # Classes are generally medium complexity
                context={
                    "docstring": cls.docstring,
                    "base_classes": cls.base_classes,
                    "methods": method_names,
                    "decorators": cls.decorators
                },
                metadata={
                    "sliced_at": datetime.now().isoformat(),
                    "analyzer_version": "1.0"
                }
            )
            slices.append(slice_obj)
        
        self.slices.extend(slices)
        logger.info(f"Sliced {len(slices)} code segments from {repo_name}")
        
        return slices
    
    def export_slices(self, output_file: Optional[str] = None) -> str:
        """
        Export slices to JSONL file
        导出切片到JSONL文件
        
        Args:
            output_file: Output file path (default: slices/code_slices_TIMESTAMP.jsonl)
            
        Returns:
            Path to exported file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"code_slices_{timestamp}.jsonl"
        else:
            output_file = Path(output_file)
        
        # Ensure directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSONL
        with open(output_file, 'w', encoding='utf-8') as f:
            for slice_obj in self.slices:
                json_line = json.dumps(slice_obj.to_dict(), ensure_ascii=False)
                f.write(json_line + '\n')
        
        logger.info(f"Exported {len(self.slices)} slices to {output_file}")
        return str(output_file)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about sliced code
        获取切片代码的统计信息
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_slices": len(self.slices),
            "by_type": {},
            "by_complexity": {},
            "by_repository": {}
        }
        
        for slice_obj in self.slices:
            # Count by type
            stats["by_type"][slice_obj.type] = stats["by_type"].get(slice_obj.type, 0) + 1
            
            # Count by complexity
            stats["by_complexity"][slice_obj.complexity] = \
                stats["by_complexity"].get(slice_obj.complexity, 0) + 1
            
            # Count by repository
            stats["by_repository"][slice_obj.repository] = \
                stats["by_repository"].get(slice_obj.repository, 0) + 1
        
        return stats
    
    def filter_slices(self, 
                     complexity: Optional[List[str]] = None,
                     type_filter: Optional[List[str]] = None,
                     min_lines: Optional[int] = None,
                     max_lines: Optional[int] = None) -> List[CodeSlice]:
        """
        Filter slices by criteria
        按条件过滤切片
        
        Args:
            complexity: List of complexity levels to include
            type_filter: List of types to include ("function", "class", "method")
            min_lines: Minimum number of lines
            max_lines: Maximum number of lines
            
        Returns:
            Filtered list of CodeSlice objects
        """
        filtered = self.slices
        
        if complexity:
            filtered = [s for s in filtered if s.complexity in complexity]
        
        if type_filter:
            filtered = [s for s in filtered if s.type in type_filter]
        
        if min_lines is not None:
            filtered = [s for s in filtered if (s.end_line - s.start_line + 1) >= min_lines]
        
        if max_lines is not None:
            filtered = [s for s in filtered if (s.end_line - s.start_line + 1) <= max_lines]
        
        return filtered

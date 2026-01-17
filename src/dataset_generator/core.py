"""
Core Dataset Generator
核心数据集生成器

Main interface for generating training datasets.
生成训练数据集的主要接口。
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..analyzers.code_analyzer import CodeAnalyzer, RepositoryCloner
from ..generators.qa_generator import QAGenerator
from ..generators.design_generator import DesignSolutionGenerator
from ..dataset_generator.models import QAPair, DesignSolution

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetGenerator:
    """Main class for generating training datasets / 生成训练数据集的主类"""
    
    def __init__(self, repo_path: str, repo_name: Optional[str] = None):
        """
        Initialize dataset generator
        
        Args:
            repo_path: Path to the repository to analyze
            repo_name: Name of the repository (owner/repo format)
        """
        self.repo_path = Path(repo_path)
        self.repo_name = repo_name or self.repo_path.name
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        logger.info(f"Initializing DatasetGenerator for {self.repo_name}")
        
        # Initialize analyzer
        self.analyzer = CodeAnalyzer(str(self.repo_path))
        self.qa_generator: Optional[QAGenerator] = None
        self.design_generator: Optional[DesignSolutionGenerator] = None
        
    def analyze_repository(self, max_files: Optional[int] = None) -> None:
        """
        Analyze the repository
        分析仓库
        
        Args:
            max_files: Maximum number of files to analyze (None for all)
        """
        logger.info("Starting repository analysis...")
        self.analyzer.analyze(max_files=max_files)
        
        # Initialize generators after analysis
        self.qa_generator = QAGenerator(self.analyzer, self.repo_name)
        self.design_generator = DesignSolutionGenerator(self.analyzer, self.repo_name)
        
        logger.info("Repository analysis complete")
    
    def generate_scenario1_dataset(self, max_pairs: int = 50, 
                                   languages: List[str] = ["en", "zh"]) -> List[QAPair]:
        """
        Generate Scenario 1 dataset (Q&A pairs)
        生成场景1数据集（问答对）
        
        Args:
            max_pairs: Maximum number of Q&A pairs to generate per language
            languages: List of languages to generate ("en", "zh")
            
        Returns:
            List of QAPair objects
        """
        if not self.qa_generator:
            raise RuntimeError("Must call analyze_repository() first")
        
        logger.info("Generating Scenario 1 dataset (Q&A pairs)...")
        qa_pairs = self.qa_generator.generate_qa_pairs(max_pairs=max_pairs, languages=languages)
        logger.info(f"Generated {len(qa_pairs)} Q&A pairs")
        
        return qa_pairs
    
    def generate_scenario2_dataset(self, max_solutions: int = 10,
                                   languages: List[str] = ["en", "zh"]) -> List[DesignSolution]:
        """
        Generate Scenario 2 dataset (Design solutions)
        生成场景2数据集（设计方案）
        
        Args:
            max_solutions: Maximum number of design solutions to generate
            languages: List of languages to generate ("en", "zh")
            
        Returns:
            List of DesignSolution objects
        """
        if not self.design_generator:
            raise RuntimeError("Must call analyze_repository() first")
        
        logger.info("Generating Scenario 2 dataset (Design solutions)...")
        solutions = self.design_generator.generate_design_solutions(
            max_solutions=max_solutions, 
            languages=languages
        )
        logger.info(f"Generated {len(solutions)} design solutions")
        
        return solutions
    
    def export_dataset(self, output_dir: str, qa_pairs: List[QAPair], 
                      solutions: List[DesignSolution], split_by_language: bool = True) -> None:
        """
        Export generated datasets to files
        导出生成的数据集到文件
        
        Args:
            output_dir: Directory to save the datasets
            qa_pairs: List of Q&A pairs to export
            solutions: List of design solutions to export
            split_by_language: Whether to split by language into separate files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exporting datasets to {output_dir}")
        
        if split_by_language:
            # Split by language
            for lang in ["en", "zh"]:
                # Export Q&A pairs
                qa_lang = [qa for qa in qa_pairs if qa.language == lang]
                if qa_lang:
                    qa_file = output_path / f"scenario1_qa_pairs_{lang}.json"
                    self._export_json(qa_file, [qa.to_dict() for qa in qa_lang])
                    logger.info(f"Exported {len(qa_lang)} Q&A pairs to {qa_file}")
                
                # Export design solutions
                sol_lang = [sol for sol in solutions if sol.language == lang]
                if sol_lang:
                    sol_file = output_path / f"scenario2_design_solutions_{lang}.json"
                    self._export_json(sol_file, [sol.to_dict() for sol in sol_lang])
                    logger.info(f"Exported {len(sol_lang)} design solutions to {sol_file}")
        else:
            # Export all together
            if qa_pairs:
                qa_file = output_path / "scenario1_qa_pairs_all.json"
                self._export_json(qa_file, [qa.to_dict() for qa in qa_pairs])
                logger.info(f"Exported {len(qa_pairs)} Q&A pairs to {qa_file}")
            
            if solutions:
                sol_file = output_path / "scenario2_design_solutions_all.json"
                self._export_json(sol_file, [sol.to_dict() for sol in solutions])
                logger.info(f"Exported {len(solutions)} design solutions to {sol_file}")
        
        # Export combined dataset
        combined = {
            "scenario1": [qa.to_dict() for qa in qa_pairs],
            "scenario2": [sol.to_dict() for sol in solutions],
            "metadata": {
                "repository": self.repo_name,
                "total_qa_pairs": len(qa_pairs),
                "total_design_solutions": len(solutions),
                "languages": ["en", "zh"]
            }
        }
        combined_file = output_path / "complete_dataset.json"
        self._export_json(combined_file, combined)
        logger.info(f"Exported complete dataset to {combined_file}")
    
    def _export_json(self, file_path: Path, data: Any) -> None:
        """Export data to JSON file / 导出数据到JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the analyzed repository
        获取分析仓库的统计信息
        
        Returns:
            Dictionary with statistics
        """
        if not self.analyzer:
            return {}
        
        return {
            "total_modules": len(self.analyzer.modules),
            "total_functions": len(self.analyzer.all_functions),
            "total_classes": len(self.analyzer.all_classes),
            "functions_by_complexity": {
                "simple": len(self.analyzer.get_functions_by_complexity("simple")),
                "medium": len(self.analyzer.get_functions_by_complexity("medium")),
                "complex": len(self.analyzer.get_functions_by_complexity("complex"))
            }
        }
    
    @staticmethod
    def from_github_url(repo_url: str, clone_dir: str, repo_name: Optional[str] = None):
        """
        Create DatasetGenerator from GitHub URL
        从GitHub URL创建数据集生成器
        
        Args:
            repo_url: GitHub repository URL
            clone_dir: Directory to clone the repository
            repo_name: Optional repository name (will extract from URL if not provided)
            
        Returns:
            DatasetGenerator instance
        """
        # Extract repo name from URL if not provided
        if not repo_name:
            # Handle URLs like https://github.com/owner/repo.git
            repo_name = repo_url.rstrip('/').rstrip('.git').split('/')[-2:]
            repo_name = '/'.join(repo_name)
        
        # Clone repository
        target_path = Path(clone_dir) / repo_name.replace('/', '_')
        RepositoryCloner.clone(repo_url, str(target_path))
        
        return DatasetGenerator(str(target_path), repo_name)

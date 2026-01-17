"""
Dataset Generator Package
训练数据集生成器包

A system for automated generation of training datasets from code repositories.
从代码仓库自动生成训练数据集的系统。
"""

__version__ = "1.0.0"
__author__ = "Dataset Generator Team"

from .core import DatasetGenerator
from .models import QAPair, DesignSolution

__all__ = ["DatasetGenerator", "QAPair", "DesignSolution"]

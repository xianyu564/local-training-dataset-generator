"""
Tests for Dataset Generator
数据集生成器测试
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dataset_generator.models import (
    CodeContext, ReasoningStep, ReasoningTrace, QAPair
)
from src.analyzers.code_analyzer import CodeAnalyzer
from src.utils.dataset_utils import (
    validate_dataset, calculate_diversity_score, split_train_test
)


class TestModels:
    """Test data models"""
    
    def test_code_context_creation(self):
        """Test CodeContext creation"""
        ctx = CodeContext(
            file_path="test.py",
            code_snippet="def test(): pass",
            start_line=1,
            end_line=1,
            function_name="test"
        )
        
        assert ctx.file_path == "test.py"
        assert ctx.function_name == "test"
        assert "file_path" in ctx.to_dict()
    
    def test_reasoning_trace_creation(self):
        """Test ReasoningTrace creation"""
        step = ReasoningStep(
            step_number=1,
            description="Test step",
            code_reference="test",
            reasoning="Test reasoning"
        )
        
        trace = ReasoningTrace(
            steps=[step],
            conclusion="Test conclusion"
        )
        
        assert len(trace.steps) == 1
        assert trace.conclusion == "Test conclusion"
    
    def test_qa_pair_creation(self):
        """Test QAPair creation"""
        ctx = CodeContext(
            file_path="test.py",
            code_snippet="def test(): pass",
            start_line=1,
            end_line=1
        )
        
        trace = ReasoningTrace(
            steps=[],
            conclusion="Test"
        )
        
        qa = QAPair(
            id="test-1",
            question="What is this?",
            answer="This is a test",
            language="en",
            code_context=ctx,
            business_rules=["rule1"],
            reasoning_trace=trace,
            metadata={"test": True}
        )
        
        assert qa.id == "test-1"
        assert qa.language == "en"
        assert qa.type == "qa_pair"
        
        # Test JSON serialization
        json_str = qa.to_json()
        assert "test-1" in json_str
        assert "qa_pair" in json_str


class TestDatasetUtils:
    """Test dataset utilities"""
    
    def test_validate_dataset(self):
        """Test dataset validation"""
        # Valid dataset
        dataset = [
            {
                "id": "1",
                "type": "qa_pair",
                "language": "en",
                "question": "Q?",
                "answer": "A",
                "code_context": {},
                "business_rules": [],
                "reasoning_trace": {},
                "metadata": {}
            }
        ]
        
        results = validate_dataset(dataset)
        assert results["total_items"] == 1
        assert results["valid_items"] == 1
        assert results["validity_rate"] == 1.0
    
    def test_validate_invalid_dataset(self):
        """Test validation with invalid data"""
        dataset = [
            {
                "id": "1",
                "type": "unknown_type"
            }
        ]
        
        results = validate_dataset(dataset)
        assert results["invalid_items"] == 1
        assert len(results["issues"]) > 0
    
    def test_diversity_score(self):
        """Test diversity score calculation"""
        dataset = [
            {
                "language": "en",
                "metadata": {
                    "complexity": "simple",
                    "tags": ["tag1", "tag2"]
                }
            },
            {
                "language": "zh",
                "metadata": {
                    "complexity": "medium",
                    "tags": ["tag3", "tag4"]
                }
            }
        ]
        
        score = calculate_diversity_score(dataset)
        assert 0.0 <= score <= 1.0
        assert score > 0.0  # Should have some diversity
    
    def test_split_train_test(self):
        """Test train/test split"""
        dataset = [{"id": i} for i in range(100)]
        
        train, test = split_train_test(dataset, test_ratio=0.2)
        
        assert len(train) == 80
        assert len(test) == 20
        assert len(train) + len(test) == len(dataset)


class TestCodeAnalyzer:
    """Test code analyzer"""
    
    def test_analyzer_creation(self):
        """Test analyzer initialization"""
        # Create temporary directory with a Python file
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
def hello(name):
    '''Say hello'''
    return f"Hello, {name}!"

class TestClass:
    '''Test class'''
    def method(self):
        pass
""")
            
            analyzer = CodeAnalyzer(tmpdir)
            analyzer.analyze()
            
            assert len(analyzer.modules) > 0
            assert len(analyzer.all_functions) > 0
            assert len(analyzer.all_classes) > 0
    
    def test_function_extraction(self):
        """Test function information extraction"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
def simple_function(x, y):
    '''Simple function'''
    return x + y
""")
            
            analyzer = CodeAnalyzer(tmpdir)
            analyzer.analyze()
            
            assert len(analyzer.all_functions) > 0
            func = analyzer.all_functions[0]
            assert func.name == "simple_function"
            assert len(func.parameters) == 2
            assert "x" in func.parameters
            assert "y" in func.parameters
            assert func.docstring == "Simple function"


def test_integration():
    """Integration test"""
    # Create a simple test repository structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test Python file
        test_file = Path(tmpdir) / "module.py"
        test_file.write_text("""
def process_data(data):
    '''Process input data'''
    if not data:
        raise ValueError("Data cannot be empty")
    return data.upper()

class DataProcessor:
    '''Processes data'''
    def __init__(self):
        self.processed = []
    
    def add(self, item):
        '''Add item to processor'''
        self.processed.append(item)
""")
        
        # Test code analysis
        analyzer = CodeAnalyzer(tmpdir)
        analyzer.analyze()
        
        assert len(analyzer.modules) == 1
        assert len(analyzer.all_functions) >= 1
        assert len(analyzer.all_classes) >= 1
        
        # Check function
        func = next((f for f in analyzer.all_functions if f.name == "process_data"), None)
        assert func is not None
        assert func.docstring == "Process input data"
        assert "data" in func.parameters
        
        # Check class
        cls = next((c for c in analyzer.all_classes if c.name == "DataProcessor"), None)
        assert cls is not None
        assert cls.docstring == "Processes data"
        assert len(cls.methods) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Unit tests for pipeline components
流水线组件的单元测试
"""

import json
import pytest
from pathlib import Path
from src.pipeline.code_slicer import CodeSlicer
from src.pipeline.batch_processor import BatchProcessor
from src.pipeline.dataset_compiler import DatasetCompiler


class TestCodeSlicer:
    """Test CodeSlicer functionality"""
    
    def test_slice_repository(self, tmp_path):
        """Test slicing a repository"""
        slicer = CodeSlicer(output_dir=str(tmp_path))
        slices = slicer.slice_repository(
            repo_path='.',
            repo_name='test/repo',
            max_files=5
        )
        
        assert len(slices) > 0
        assert all(hasattr(s, 'id') for s in slices)
        assert all(hasattr(s, 'code_snippet') for s in slices)
    
    def test_export_slices(self, tmp_path):
        """Test exporting slices to JSONL"""
        slicer = CodeSlicer(output_dir=str(tmp_path))
        slicer.slice_repository('.', 'test/repo', max_files=3)
        
        output_file = slicer.export_slices()
        assert Path(output_file).exists()
        
        # Verify JSONL format
        with open(output_file) as f:
            for line in f:
                data = json.loads(line)
                assert 'id' in data
                assert 'code_snippet' in data
    
    def test_get_statistics(self, tmp_path):
        """Test statistics generation"""
        slicer = CodeSlicer(output_dir=str(tmp_path))
        slicer.slice_repository('.', 'test/repo', max_files=3)
        
        stats = slicer.get_statistics()
        assert 'total_slices' in stats
        assert 'by_type' in stats
        assert 'by_complexity' in stats


class TestBatchProcessor:
    """Test BatchProcessor functionality"""
    
    def test_create_scenario1_prompts(self, tmp_path):
        """Test creating Scenario 1 prompts"""
        processor = BatchProcessor(
            config_path='nonexistent.yaml',
            output_dir=str(tmp_path)
        )
        
        dummy_slices = [
            {
                'id': 'test_001',
                'type': 'function',
                'code_snippet': 'def example(): pass',
                'file_path': 'test.py',
                'name': 'example',
                'complexity': 'simple',
                'context': {}
            }
        ]
        
        requests = processor.create_scenario1_prompts(dummy_slices)
        assert len(requests) == 1
        assert requests[0].custom_id.startswith('scenario1_')
    
    def test_create_scenario2_prompts(self, tmp_path):
        """Test creating Scenario 2 prompts"""
        processor = BatchProcessor(
            config_path='nonexistent.yaml',
            output_dir=str(tmp_path)
        )
        
        dummy_slices = [
            {
                'id': 'test_001',
                'type': 'class',
                'code_snippet': 'class Example: pass',
                'file_path': 'test.py',
                'name': 'Example',
                'complexity': 'medium',
                'context': {}
            }
        ]
        
        requests = processor.create_scenario2_prompts(dummy_slices)
        assert len(requests) == 1
        assert requests[0].custom_id.startswith('scenario2_')
    
    def test_export_batch_requests(self, tmp_path):
        """Test exporting batch requests"""
        processor = BatchProcessor(
            config_path='nonexistent.yaml',
            output_dir=str(tmp_path)
        )
        
        dummy_slices = [
            {
                'id': 'test_001',
                'type': 'function',
                'code_snippet': 'def test(): pass',
                'file_path': 'test.py',
                'name': 'test',
                'complexity': 'simple',
                'context': {}
            }
        ]
        
        requests = processor.create_scenario1_prompts(dummy_slices)
        output_file = processor.export_batch_requests(requests, 'scenario1')
        
        assert Path(output_file).exists()
        
        # Verify JSONL format
        with open(output_file) as f:
            data = json.loads(f.readline())
            assert 'custom_id' in data
            assert 'method' in data
            assert 'body' in data


class TestDatasetCompiler:
    """Test DatasetCompiler functionality"""
    
    def test_load_scenario_data(self, tmp_path):
        """Test loading scenario data"""
        # Create test data files
        scenario1_file = tmp_path / 'scenario1.jsonl'
        with open(scenario1_file, 'w') as f:
            f.write(json.dumps({
                'id': 'test_1',
                'question': 'Test?',
                'answer': 'Answer',
                'reasoning_trace': {'steps': [], 'conclusion': 'test'}
            }) + '\n')
        
        scenario2_file = tmp_path / 'scenario2.jsonl'
        with open(scenario2_file, 'w') as f:
            f.write(json.dumps({
                'id': 'test_2',
                'requirement': {'title': 'Test'},
                'design_solution': {'overview': 'Test'},
                'reasoning_trace': {'decision_points': []}
            }) + '\n')
        
        compiler = DatasetCompiler(output_dir=str(tmp_path / 'output'))
        compiler.load_scenario_data(
            scenario1_file=str(scenario1_file),
            scenario2_file=str(scenario2_file)
        )
        
        assert len(compiler.scenario1_data) == 1
        assert len(compiler.scenario2_data) == 1
    
    def test_generate_statistics(self, tmp_path):
        """Test statistics generation"""
        compiler = DatasetCompiler(output_dir=str(tmp_path))
        compiler.scenario1_data = [{'id': '1', 'complexity': 'simple'}]
        compiler.scenario2_data = [{'id': '2'}]
        
        stats = compiler.generate_statistics()
        assert stats['scenario1']['total_count'] == 1
        assert stats['scenario2']['total_count'] == 1
        assert stats['combined']['total_items'] == 2
    
    def test_export_training_dataset(self, tmp_path):
        """Test exporting training dataset"""
        compiler = DatasetCompiler(output_dir=str(tmp_path))
        compiler.scenario1_data = [{'id': '1', 'question': 'Q1'}]
        compiler.scenario2_data = [{'id': '2', 'requirement': 'R1'}]
        
        output_file = compiler.export_training_dataset(shuffle=True, seed=42)
        assert Path(output_file).exists()
        
        # Verify JSONL format and training_scenario marker
        with open(output_file) as f:
            for line in f:
                data = json.loads(line)
                assert 'training_scenario' in data
                assert data['training_scenario'] in ['scenario1_qa', 'scenario2_design']

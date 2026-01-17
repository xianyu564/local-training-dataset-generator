"""
Configuration loader utility
配置加载工具
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration loader for the pipeline"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Load configuration from YAML file
        
        Args:
            config_path: Path to config.yaml file
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load configuration from file"""
        if not self.config_path.exists():
            # Use default configuration if file doesn't exist
            logger = logging.getLogger(__name__)
            logger.warning(f"Config file not found: {self.config_path}. Using defaults.")
            self._config = self._get_defaults()
            return
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration / 获取默认配置"""
        return {
            'pipeline': {
                'slices_dir': 'slices',
                'reviewed_slices_dir': 'reviewed_slices',
                'batch_input_dir': 'batch_input',
                'batch_output_dir': 'batch_output',
                'final_output_dir': 'final_output',
                'repositories': [],
                'max_scenario1_items': 100,
                'max_scenario2_items': 50,
                'shuffle_dataset': True,
                'random_seed': 42
            },
            'repository': {
                'clone_dir': '/tmp/datasets'
            },
            'output': {
                'format': 'jsonl'
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key
        
        Args:
            key: Configuration key (supports nested keys with dots, e.g., "pipeline.slices_dir")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    @property
    def pipeline(self) -> Dict[str, Any]:
        """Get pipeline configuration"""
        return self._config.get('pipeline', {})
    
    @property
    def analysis(self) -> Dict[str, Any]:
        """Get analysis configuration"""
        return self._config.get('analysis', {})
    
    @property
    def generation(self) -> Dict[str, Any]:
        """Get generation configuration"""
        return self._config.get('generation', {})
    
    @property
    def quality(self) -> Dict[str, Any]:
        """Get quality configuration"""
        return self._config.get('quality', {})
    
    @property
    def output(self) -> Dict[str, Any]:
        """Get output configuration"""
        return self._config.get('output', {})
    
    @property
    def repository(self) -> Dict[str, Any]:
        """Get repository configuration"""
        return self._config.get('repository', {})
    
    @property
    def logging(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self._config.get('logging', {})


# Global config instance
_config_instance: Optional[Config] = None


def get_config(config_path: str = "config.yaml") -> Config:
    """
    Get global config instance
    
    Args:
        config_path: Path to config file
        
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance


def reload_config(config_path: str = "config.yaml") -> Config:
    """
    Reload configuration from file
    
    Args:
        config_path: Path to config file
        
    Returns:
        New Config instance
    """
    global _config_instance
    _config_instance = Config(config_path)
    return _config_instance

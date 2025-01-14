import pytest
from pathlib import Path
from src.utils.config_manager import ConfigManager

def test_config_manager_init():
    config = ConfigManager()
    assert config.config is not None
    assert isinstance(config.config, dict)

def test_config_get_set():
    config = ConfigManager()
    
    # 测试设置和获取API密钥
    assert config.set('api.key', 'test_key')
    assert config.get('api.key') == 'test_key'
    
    # 测试获取默认值
    assert config.get('not.exist', 'default') == 'default'
    
    # 测试设置UI配置
    assert config.set('ui.theme', 'dark')
    assert config.get('ui.theme') == 'dark'

def test_config_file_creation():
    config = ConfigManager()
    config_file = Path.home() / '.image_generator' / 'config.json'
    assert config_file.exists() 
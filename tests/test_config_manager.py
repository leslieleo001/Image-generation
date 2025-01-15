import os
import pytest
import shutil
from pathlib import Path
from src.utils.config_manager import ConfigManager

@pytest.fixture
def temp_dir(tmp_path):
    """创建临时测试目录"""
    yield tmp_path
    # 清理临时目录
    if tmp_path.exists():
        shutil.rmtree(tmp_path)

def test_directory_creation(temp_dir):
    """测试目录创建功能"""
    config_manager = ConfigManager()
    
    # 验证所有必要的目录是否存在
    assert os.path.exists(config_manager.config_dir)
    assert os.path.exists(config_manager.defaults["paths"]["output_dir"])
    assert os.path.exists(config_manager.defaults["paths"]["presets_dir"])
    assert os.path.exists(os.path.dirname(config_manager.defaults["paths"]["history_file"]))

def test_config_save_and_load():
    """测试配置保存和加载功能"""
    config_manager = ConfigManager()
    
    # 测试保存配置
    test_api_key = "test_key_123"
    assert config_manager.set("api_key", test_api_key)
    
    # 验证配置文件是否存在
    assert os.path.exists(config_manager.config_file)
    
    # 创建新的配置管理器实例来测试加载
    new_config_manager = ConfigManager()
    assert new_config_manager.get("api_key") == test_api_key

def test_config_merge():
    """测试配置合并功能"""
    config_manager = ConfigManager()
    
    # 修改一些配置
    test_config = {
        "api_key": "test_key_456",
        "defaults": {
            "model": "test_model",
            "size": "512x512"
        }
    }
    
    # 保存测试配置
    assert config_manager.save_config(test_config)
    
    # 重新加载配置
    new_config_manager = ConfigManager()
    
    # 验证修改的配置是否保留
    assert new_config_manager.get("api_key") == "test_key_456"
    assert new_config_manager.get("defaults.model") == "test_model"
    assert new_config_manager.get("defaults.size") == "512x512"
    
    # 验证默认配置是否存在
    assert new_config_manager.get("defaults.steps") == 20
    assert new_config_manager.get("defaults.guidance") == 7.5

def test_config_error_handling():
    """测试错误处理功能"""
    config_manager = ConfigManager()
    
    # 测试无效的配置键
    assert config_manager.get("invalid_key") is None
    
    # 测试设置无效的配置
    assert not config_manager.set(None, "value")
    
    # 测试嵌套配置访问
    assert config_manager.get("defaults.invalid_key") is None

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 
import pytest
import json
import os
from pathlib import Path
from unittest.mock import MagicMock
from src.utils.preset_manager import PresetManager

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.get.return_value = "test_presets"
    return config

@pytest.fixture
def preset_manager(mock_config, tmp_path):
    # 使用临时目录作为预设目录
    mock_config.get.return_value = str(tmp_path / "presets")
    manager = PresetManager(mock_config)
    yield manager
    # 清理测试文件
    for file in Path(manager.presets_dir).glob("*.json"):
        file.unlink()

@pytest.fixture
def sample_preset():
    return {
        "name": "测试预设",
        "params": {
            "prompt": "测试提示词",
            "model": "stable-diffusion-3",
            "size": "1024x1024",
            "steps": 20,
            "guidance_scale": 7.5,
            "description": "测试描述"
        }
    }

def test_init(preset_manager):
    """测试初始化"""
    assert preset_manager.config is not None
    assert preset_manager.presets_dir.exists()
    assert isinstance(preset_manager._presets, dict)

def test_save_preset(preset_manager, sample_preset):
    """测试保存预设"""
    # 保存预设
    result = preset_manager.save_preset(
        sample_preset["name"],
        sample_preset["params"]
    )
    assert result is True
    
    # 验证文件是否创建
    file_path = preset_manager.presets_dir / f"{sample_preset['name']}.json"
    assert file_path.exists()
    
    # 验证内容
    with open(file_path, "r", encoding="utf-8") as f:
        saved_preset = json.load(f)
        assert saved_preset["name"] == sample_preset["name"]
        assert saved_preset["params"] == sample_preset["params"]

def test_load_presets(preset_manager, sample_preset):
    """测试加载预设"""
    # 先保存一个预设
    preset_manager.save_preset(sample_preset["name"], sample_preset["params"])
    
    # 创建新的管理器实例来测试加载
    new_manager = PresetManager(preset_manager.config)
    
    # 验证预设是否被加载
    assert sample_preset["name"] in new_manager._presets
    loaded_preset = new_manager._presets[sample_preset["name"]]
    assert loaded_preset["params"] == sample_preset["params"]

def test_get_preset(preset_manager, sample_preset):
    """测试获取预设"""
    # 保存预设
    preset_manager.save_preset(sample_preset["name"], sample_preset["params"])
    
    # 获取预设
    preset = preset_manager.get_preset(sample_preset["name"])
    assert preset == sample_preset["params"]
    
    # 测试获取不存在的预设
    assert preset_manager.get_preset("不存在") is None

def test_list_presets(preset_manager, sample_preset):
    """测试列出所有预设"""
    # 保存多个预设
    preset_manager.save_preset(sample_preset["name"], sample_preset["params"])
    preset_manager.save_preset("预设2", {"prompt": "测试2"})
    
    # 获取预设列表
    presets = preset_manager.list_presets()
    assert len(presets) == 2
    assert any(p["name"] == sample_preset["name"] for p in presets)
    assert any(p["name"] == "预设2" for p in presets)

def test_delete_preset(preset_manager, sample_preset):
    """测试删除预设"""
    # 保存预设
    preset_manager.save_preset(sample_preset["name"], sample_preset["params"])
    
    # 删除预设
    result = preset_manager.delete_preset(sample_preset["name"])
    assert result is True
    
    # 验证预设已被删除
    assert sample_preset["name"] not in preset_manager._presets
    file_path = preset_manager.presets_dir / f"{sample_preset['name']}.json"
    assert not file_path.exists()
    
    # 测试删除不存在的预设
    assert preset_manager.delete_preset("不存在") is False

def test_update_preset(preset_manager, sample_preset):
    """测试更新预设"""
    # 保存预设
    preset_manager.save_preset(sample_preset["name"], sample_preset["params"])
    
    # 更新预设
    new_params = sample_preset["params"].copy()
    new_params["prompt"] = "新的提示词"
    result = preset_manager.update_preset(sample_preset["name"], new_params)
    assert result is True
    
    # 验证更新结果
    updated_preset = preset_manager.get_preset(sample_preset["name"])
    assert updated_preset["prompt"] == "新的提示词"
    
    # 测试更新不存在的预设
    assert preset_manager.update_preset("不存在", {}) is False

def test_import_export_presets(preset_manager, sample_preset, tmp_path):
    """测试导入导出预设"""
    # 保存预设
    preset_manager.save_preset(sample_preset["name"], sample_preset["params"])
    preset_manager.save_preset("预设2", {"prompt": "测试2"})
    
    # 导出预设
    export_path = tmp_path / "export.json"
    result = preset_manager.export_presets(str(export_path))
    assert result is True
    assert export_path.exists()
    
    # 清空当前预设
    preset_manager._presets.clear()
    assert len(preset_manager.list_presets()) == 0
    
    # 导入预设
    result = preset_manager.import_presets(str(export_path))
    assert result is True
    
    # 验证导入结果
    presets = preset_manager.list_presets()
    assert len(presets) == 2
    assert any(p["name"] == sample_preset["name"] for p in presets)
    assert any(p["name"] == "预设2" for p in presets)

def test_export_selected_presets(preset_manager, sample_preset, tmp_path):
    """测试导出选定的预设"""
    # 保存多个预设
    preset_manager.save_preset(sample_preset["name"], sample_preset["params"])
    preset_manager.save_preset("预设2", {"prompt": "测试2"})
    preset_manager.save_preset("预设3", {"prompt": "测试3"})
    
    # 导出选定的预设
    export_path = tmp_path / "export_selected.json"
    result = preset_manager.export_presets(
        str(export_path),
        [sample_preset["name"], "预设2"]
    )
    assert result is True
    
    # 验证导出结果
    with open(export_path, "r", encoding="utf-8") as f:
        exported = json.load(f)
        assert len(exported) == 2
        assert any(p["name"] == sample_preset["name"] for p in exported)
        assert any(p["name"] == "预设2" for p in exported)
        assert not any(p["name"] == "预设3" for p in exported)

def test_error_handling(preset_manager, sample_preset, tmp_path):
    """测试错误处理"""
    # 创建并写入一个只读文件
    readonly_file = preset_manager.presets_dir / "readonly.json"
    with open(readonly_file, "w") as f:
        f.write("{}")
    os.chmod(readonly_file, 0o444)  # 设置为只读
    
    # 测试更新只读文件
    result = preset_manager.save_preset("readonly", sample_preset["params"])
    assert result is False
    
    # 测试加载损坏的JSON文件
    corrupt_file = preset_manager.presets_dir / "corrupt.json"
    with open(corrupt_file, "w") as f:
        f.write("invalid json")
    new_manager = PresetManager(preset_manager.config)
    assert "corrupt" not in new_manager._presets
    
    # 测试导入无效文件
    assert preset_manager.import_presets("nonexistent.json") is False
    
    # 测试导出到只读文件
    export_file = preset_manager.presets_dir / "export.json"
    with open(export_file, "w") as f:
        f.write("{}")
    os.chmod(export_file, 0o444)
    assert preset_manager.export_presets(str(export_file)) is False
    
    # 清理：恢复文件权限以便删除
    os.chmod(readonly_file, 0o666)
    os.chmod(export_file, 0o666) 
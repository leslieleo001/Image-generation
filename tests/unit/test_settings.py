import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox, QLineEdit
from PyQt6.QtCore import Qt
from src.ui.settings import SettingsTab
from src.utils.config_manager import ConfigManager
from src.utils.api_manager import APIManager
from unittest.mock import MagicMock, patch

@pytest.fixture(scope="session")
def app():
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def mock_config():
    config = ConfigManager()
    config.defaults = {
        "api_key": "",
        "models": [
            "stabilityai/stable-diffusion-3-5-large",
            "stabilityai/stable-diffusion-3-medium",
            "stabilityai/stable-diffusion-3-5-large-turbo"
        ],
        "defaults": {
            "model": "stabilityai/stable-diffusion-3-5-large",
            "size": "1024x1024",
            "steps": 20,
            "guidance": 7.5,
            "enhance": False,
            "negative_prompt": "",
            "batch_size": 1,
            "seed": -1,
            "use_random_seed": False
        },
        "paths": {
            "output_dir": "",
            "presets_dir": "presets",
            "history_file": "history.json"
        },
        "history": {
            "max_items": 100
        },
        "naming_rule": {
            "preset": "默认",
            "custom": "{timestamp}_{prompt}_{model}_{size}_{seed}"
        }
    }
    config.config = config.defaults.copy()
    return config

@pytest.fixture
def settings_tab(app, qtbot, mock_config):
    api_manager = APIManager(mock_config)
    settings = SettingsTab(mock_config, api_manager)
    qtbot.addWidget(settings)
    yield settings
    settings.deleteLater()
    app.processEvents()

def test_settings_init(settings_tab):
    """测试设置界面初始化"""
    # 验证API密钥输入框
    assert settings_tab.api_key_input.placeholderText() == "请输入API密钥"
    assert settings_tab.api_key_input.echoMode() == QLineEdit.EchoMode.Password
    
    # 验证按钮
    assert settings_tab.test_api_btn.text() == "测试API"
    assert settings_tab.save_btn.text() == "保存设置"
    assert settings_tab.select_dir_btn.text() == "浏览..."

def test_save_settings(settings_tab, monkeypatch):
    """测试保存设置"""
    # 模拟QMessageBox
    mock_message_box = MagicMock()
    monkeypatch.setattr(QMessageBox, 'information', mock_message_box)
    
    # 设置测试数据
    settings_tab.api_key_input.setText("test_key")
    settings_tab.output_dir.setText("/test/path")
    
    # 保存设置
    settings_tab.save_settings()
    
    # 验证配置是否正确保存
    assert settings_tab.config.get("api_key") == "test_key"
    assert settings_tab.config.get("paths.output_dir") == "/test/path"
    
    # 验证是否显示成功消息
    mock_message_box.assert_called_once()

@patch('src.utils.api_client.SiliconFlowAPI.validate_api_key')
def test_test_api_key_success(mock_validate, settings_tab, monkeypatch, qtbot):
    """测试API密钥验证成功"""
    # 模拟API验证成功
    mock_validate.return_value = True
    
    # 模拟QMessageBox
    mock_message_box = MagicMock()
    monkeypatch.setattr(QMessageBox, 'information', mock_message_box)
    
    # 设置API密钥并测试
    settings_tab.api_key_input.setText("valid_key")
    qtbot.mouseClick(settings_tab.test_api_btn, Qt.MouseButton.LeftButton)
    
    # 等待测试线程完成
    qtbot.wait(100)  # 等待线程启动和完成
    
    # 验证API验证方法是否被调用
    mock_validate.assert_called_once()
    # 验证是否显示成功消息
    mock_message_box.assert_called_once_with(settings_tab, "成功", "API密钥验证成功")

@patch('src.utils.api_client.SiliconFlowAPI.validate_api_key')
def test_test_api_key_failure(mock_validate, settings_tab, monkeypatch, qtbot):
    """测试API密钥验证失败"""
    # 模拟API验证失败
    mock_validate.return_value = False
    
    # 模拟QMessageBox
    mock_message_box = MagicMock()
    monkeypatch.setattr(QMessageBox, 'critical', mock_message_box)
    
    # 设置API密钥并测试
    settings_tab.api_key_input.setText("invalid_key")
    qtbot.mouseClick(settings_tab.test_api_btn, Qt.MouseButton.LeftButton)
    
    # 等待测试线程完成
    qtbot.wait(100)  # 等待线程启动和完成
    
    # 验证API验证方法是否被调用
    mock_validate.assert_called_once()
    # 验证是否显示错误消息
    mock_message_box.assert_called_once_with(settings_tab, "错误", "API密钥无效")

def test_test_api_key_empty(settings_tab, monkeypatch, qtbot):
    """测试空API密钥"""
    # 模拟QMessageBox
    mock_message_box = MagicMock()
    monkeypatch.setattr(QMessageBox, 'warning', mock_message_box)
    
    # 清空API密钥并测试
    settings_tab.api_key_input.setText("")
    qtbot.mouseClick(settings_tab.test_api_btn, Qt.MouseButton.LeftButton)
    
    # 验证是否显示警告消息
    mock_message_box.assert_called_once_with(settings_tab, "警告", "请先输入API密钥")

def test_default_seed_setting(settings_tab):
    """测试默认种子值设置"""
    # 测试初始状态
    assert settings_tab.default_seed_input.text() == ""  # 显示为空
    assert settings_tab.default_random_seed_check.isChecked() == False  # 默认不选中
    
    # 测试随机种子开关
    settings_tab.default_random_seed_check.setChecked(True)
    assert not settings_tab.default_seed_input.isEnabled()  # 输入框禁用
    assert settings_tab.default_seed_input.text() == ""  # 值清空
    
    # 测试固定种子值
    settings_tab.default_random_seed_check.setChecked(False)
    settings_tab.default_seed_input.setText("42")
    assert settings_tab.default_seed_input.isEnabled()  # 输入框启用
    assert settings_tab.default_seed_input.text() == "42"  # 值设置正确
    
    # 测试种子值范围验证
    settings_tab.default_seed_input.setText("0")  # 小于最小值
    assert settings_tab.default_seed_input.text() == "1"  # 自动修正为最小值
    
    settings_tab.default_seed_input.setText("9999999999")  # 大于最大值
    assert settings_tab.default_seed_input.text() == "9999999998"  # 自动修正为最大值
    
    settings_tab.default_seed_input.setText("abc")  # 非数字
    assert settings_tab.default_seed_input.text() == ""  # 清除非法输入 
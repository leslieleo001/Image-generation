import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox, QLineEdit
from PyQt6.QtCore import Qt
from src.ui.settings import SettingsTab
from unittest.mock import MagicMock, patch

@pytest.fixture(scope="session")
def app():
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def settings_tab(app, qtbot):
    settings = SettingsTab()
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
    assert settings_tab.select_dir_btn.text() == "选择"

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
    assert settings_tab.config.get("api.key") == "test_key"
    assert settings_tab.config.get("paths.output_dir") == "/test/path"
    
    # 验证是否显示成功消息
    mock_message_box.assert_called_once()

@patch('src.ui.settings.SiliconFlowAPI')
def test_test_api_key_success(mock_api, settings_tab):
    """测试API密钥验证成功"""
    # 模拟API验证成功
    mock_api_instance = MagicMock()
    mock_api_instance.validate_api_key.return_value = True
    mock_api.return_value = mock_api_instance
    
    # 设置API密钥并测试
    settings_tab.api_key_input.setText("valid_key")
    settings_tab.test_api_key()
    
    # 验证API验证方法是否被调用
    mock_api_instance.validate_api_key.assert_called_once()

@patch('src.ui.settings.SiliconFlowAPI')
def test_test_api_key_failure(mock_api, settings_tab):
    """测试API密钥验证失败"""
    # 模拟API验证失败
    mock_api_instance = MagicMock()
    mock_api_instance.validate_api_key.return_value = False
    mock_api.return_value = mock_api_instance
    
    # 设置API密钥并测试
    settings_tab.api_key_input.setText("invalid_key")
    settings_tab.test_api_key()
    
    # 验证API验证方法是否被调用
    mock_api_instance.validate_api_key.assert_called_once() 
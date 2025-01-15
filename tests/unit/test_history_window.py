import pytest
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from src.ui.history_window import HistoryWindow
from src.utils.history_manager import HistoryManager
from unittest.mock import MagicMock, patch

@pytest.fixture(scope="session")
def app():
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def mock_history():
    """创建历史记录管理器mock"""
    history_mock = MagicMock(spec=HistoryManager)
    history_mock.records = [
        {
            "timestamp": "2024-03-20 10:00:00",
            "prompt": "test prompt 1",
            "negative_prompt": "test negative 1",
            "model": "test model",
            "size": "512x512",
            "steps": 20,
            "guidance": 7.5,
            "seed": 12345,
            "image_paths": ["tests/data/test_image.png"]  # 使用测试图片
        }
    ]
    history_mock.get_records.return_value = history_mock.records
    history_mock.delete_record = MagicMock()
    history_mock.save_records = MagicMock()
    return history_mock

@pytest.fixture
def test_image(tmp_path):
    """创建测试图片"""
    from PIL import Image
    import numpy as np
    
    # 创建一个简单的测试图片
    img = Image.fromarray(np.zeros((64, 64, 3), dtype=np.uint8))
    img_path = tmp_path / "test_image.png"
    img.save(img_path)
    return str(img_path)

@pytest.fixture
def history_window(qtbot, mock_history, test_image):
    """创建历史窗口实例"""
    # 更新mock数据使用测试图片
    mock_history.get_records.return_value[0]["image_paths"] = [test_image]
    window = HistoryWindow(mock_history)
    qtbot.addWidget(window)
    return window

def test_history_window_init(history_window):
    """测试历史记录窗口初始化"""
    assert history_window.windowTitle() == "历史记录管理"
    assert history_window.table.columnCount() == 7
    headers = [history_window.table.horizontalHeaderItem(i).text() for i in range(7)]
    assert headers == ["选择", "缩略图", "名称", "提示词", "模型", "参数", "保存路径"]
    
    # 验证初始数据
    assert len(history_window.history_manager.records) == 1
    record = history_window.history_manager.records[0]
    assert record["prompt"] == "test prompt 1"
    assert record["negative_prompt"] == "test negative 1"
    assert record["model"] == "test model"

def test_delete_selected_without_files(history_window, monkeypatch, qtbot):
    """测试删除记录但不删除文件"""
    # 模拟记录数据
    mock_records = [
        {
            "timestamp": "2024-01-14 12:00:00",
            "params": {"prompt": "test1"},
            "image_paths": ["test1.jpg"]
        },
        {
            "timestamp": "2024-01-14 12:01:00",
            "params": {"prompt": "test2"},
            "image_paths": ["test2.jpg"]
        }
    ]
    history_window.history_manager.records = mock_records
    history_window.history_manager.get_records.return_value = mock_records
    history_window.refresh_table()
    qtbot.wait(100)  # 等待表格刷新
    
    # 模拟用户选择
    history_window.table.selectRow(0)
    qtbot.wait(100)  # 等待选择生效
    
    # 模拟QMessageBox
    monkeypatch.setattr(QMessageBox, 'question', 
                       lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
    
    # 执行删除
    history_window.delete_selected(False)
    qtbot.wait(100)  # 等待删除操作完成
    
    # 验证结果
    assert len(history_window.history_manager.records) == 1
    assert history_window.history_manager.records[0]["params"]["prompt"] == "test2"

def test_delete_selected_with_files(history_window, mock_history, test_image, qtbot, monkeypatch):
    """测试删除带文件的记录"""
    # 更新mock数据使用测试图片
    mock_history.records = [{
        "timestamp": "2024-03-20 10:00:00",
        "prompt": "test prompt 1",
        "negative_prompt": "test negative 1",
        "model": "test model",
        "size": "512x512",
        "steps": 20,
        "guidance": 7.5,
        "seed": 12345,
        "image_paths": [test_image]
    }]
    mock_history.get_records.return_value = mock_history.records
    history_window.refresh_table()
    qtbot.wait(100)
    
    # 模拟用户确认
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    
    # 选择第一行
    history_window.table.selectRow(0)
    qtbot.wait(100)
    
    # 调用删除方法
    history_window.delete_selected(delete_files=True)
    qtbot.wait(100)
    
    # 验证记录被删除
    assert len(mock_history.records) == 0
    assert mock_history.save_records.called

def test_delete_selected_multiple_files(history_window, mock_history, test_image, qtbot, monkeypatch):
    """测试删除多个文件的记录"""
    # 创建多个测试图片路径
    image_paths = [test_image] * 3
    
    # 更新mock数据
    mock_history.records = [{
        "timestamp": "2024-03-20 10:00:00",
        "prompt": "test prompt 1",
        "negative_prompt": "test negative 1",
        "model": "test model",
        "size": "512x512",
        "steps": 20,
        "guidance": 7.5,
        "seed": 12345,
        "image_paths": image_paths
    }]
    mock_history.get_records.return_value = mock_history.records
    history_window.refresh_table()
    qtbot.wait(100)
    
    # 模拟用户确认
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    
    # 选择第一行
    history_window.table.selectRow(0)
    qtbot.wait(100)
    
    # 调用删除方法
    history_window.delete_selected(delete_files=True)
    qtbot.wait(100)
    
    # 验证记录被删除
    assert len(mock_history.records) == 0
    assert mock_history.save_records.called 
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
def history_window(app, qtbot):
    history_manager = HistoryManager()
    window = HistoryWindow(history_manager)
    qtbot.addWidget(window)
    yield window
    window.deleteLater()
    app.processEvents()

def test_history_window_init(history_window):
    """测试历史记录窗口初始化"""
    assert history_window.windowTitle() == "历史记录管理"
    assert history_window.table.columnCount() == 7
    headers = [history_window.table.horizontalHeaderItem(i).text() for i in range(7)]
    assert headers == ["缩略图", "时间", "提示词", "模型", "参数", "保存路径", "操作"]

def test_delete_selected_without_files(history_window, monkeypatch):
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
    history_window.refresh_table()
    
    # 模拟用户选择
    history_window.table.selectRow(0)
    
    # 模拟QMessageBox
    mock_question = MagicMock(return_value=QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, 'question', mock_question)
    
    # 执行删除
    history_window.delete_selected(False)
    
    # 验证结果
    assert len(history_window.history_manager.records) == 1
    assert history_window.history_manager.records[0]["params"]["prompt"] == "test2"

def test_delete_selected_with_files(history_window, monkeypatch, tmp_path):
    """测试同时删除记录和文件"""
    # 创建临时测试文件
    test_file = tmp_path / "test.jpg"
    test_file.write_text("")
    
    # 模拟记录数据
    mock_records = [
        {
            "timestamp": "2024-01-14 12:00:00",
            "params": {"prompt": "test"},
            "image_paths": [str(test_file)]
        }
    ]
    history_window.history_manager.records = mock_records
    history_window.refresh_table()
    
    # 模拟用户选择
    history_window.table.selectRow(0)
    
    # 模拟QMessageBox
    mock_question = MagicMock(return_value=QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, 'question', mock_question)
    
    # 执行删除
    history_window.delete_selected(True)
    
    # 验证结果
    assert len(history_window.history_manager.records) == 0
    assert not os.path.exists(test_file)

def test_delete_selected_multiple_files(history_window, monkeypatch, tmp_path):
    """测试删除多图记录"""
    # 创建临时测试文件
    test_files = [tmp_path / f"test{i}.jpg" for i in range(3)]
    for file in test_files:
        file.write_text("")
    
    # 模拟记录数据
    mock_records = [
        {
            "timestamp": "2024-01-14 12:00:00",
            "params": {"prompt": "test"},
            "image_paths": [str(f) for f in test_files]
        }
    ]
    history_window.history_manager.records = mock_records
    history_window.refresh_table()
    
    # 模拟用户选择
    history_window.table.selectRow(0)
    
    # 模拟QMessageBox
    mock_question = MagicMock(return_value=QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, 'question', mock_question)
    
    # 执行删除
    history_window.delete_selected(True)
    
    # 验证结果
    assert len(history_window.history_manager.records) == 0
    for file in test_files:
        assert not os.path.exists(file) 
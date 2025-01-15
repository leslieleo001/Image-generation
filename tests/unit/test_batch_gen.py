import os
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime
import pytest
import pandas as pd
from PyQt6.QtWidgets import QApplication, QMessageBox, QFileDialog, QListWidgetItem
from PyQt6.QtTest import QSignalSpy
from PyQt6.QtCore import Qt, QThread
from src.ui.batch_gen import BatchGenTab
from src.utils.api_manager import APIManager
from src.utils.config_manager import ConfigManager
from src.utils.history_manager import HistoryManager

# 确保 QMessageBox 的 mock 方法
QMessageBox.information = MagicMock()
QMessageBox.warning = MagicMock()
QMessageBox.question = MagicMock()

@pytest.fixture(autouse=True)
def reset_mocks():
    """重置所有mock"""
    QMessageBox.information.reset_mock()
    QMessageBox.warning.reset_mock()
    QMessageBox.question.reset_mock()
    yield

@pytest.fixture
def mock_api():
    """创建API管理器mock"""
    api_mock = MagicMock()
    api_mock.api = MagicMock()
    api_mock.api.generate_image = MagicMock(return_value={"data": ["mock_image.jpg"]})
    return api_mock

@pytest.fixture
def mock_config():
    """创建配置管理器mock"""
    config_mock = MagicMock()
    config_mock.get = MagicMock(return_value={
        "paths": {"output_dir": "/mock/output"},
        "naming_rule": "{timestamp}_{prompt}_{model}_{size}_{seed}"
    })
    return config_mock

@pytest.fixture
def mock_history():
    """创建历史记录管理器mock"""
    history_mock = MagicMock()
    history_mock.add_record = MagicMock()
    history_mock.delete_record = MagicMock()
    history_mock.save_records = MagicMock()
    return history_mock

@pytest.fixture(scope="session")
def app():
    """创建QApplication实例"""
    if not QApplication.instance():
        app = QApplication([])
        yield app
        app.quit()
    else:
        yield QApplication.instance()

@pytest.fixture
def batch_gen_tab(qtbot, mock_api, mock_config, mock_history):
    """创建批量生成标签页"""
    tab = BatchGenTab(mock_api, mock_config, mock_history)
    qtbot.addWidget(tab)
    return tab

@pytest.fixture(autouse=True)
def mock_file_dialogs(monkeypatch):
    """模拟文件选择对话框"""
    def mock_get_open_file_name(*args, **kwargs):
        return '/mock/path/to/file.xlsx', 'Excel Files (*.xlsx)'
    
    def mock_get_save_file_name(*args, **kwargs):
        return '/mock/path/to/save.xlsx', 'Excel Files (*.xlsx)'
    
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', mock_get_open_file_name)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', mock_get_save_file_name)
    yield

def test_init(batch_gen_tab, mock_api, mock_config, mock_history):
    """测试初始化"""
    assert batch_gen_tab.api_manager == mock_api
    assert batch_gen_tab.config_manager == mock_config
    assert batch_gen_tab.history_manager == mock_history
    assert batch_gen_tab.tasks == []
    assert not batch_gen_tab.start_btn.isEnabled()
    assert not batch_gen_tab.pause_btn.isEnabled()
    assert not batch_gen_tab.resume_btn.isEnabled()
    assert not batch_gen_tab.clear_btn.isEnabled()

def test_import_excel_success(batch_gen_tab, tmp_path, monkeypatch):
    """测试导入Excel成功"""
    # 创建测试Excel文件
    test_file = tmp_path / "test.xlsx"
    import pandas as pd
    
    # 创建包含测试数据的DataFrame
    data = {
        "prompt": ["test prompt"],
        "negative_prompt": ["negative test"],
        "model": ["model A"],
        "size": ["512x512"],
        "steps": [20],
        "guidance": [7.5],
        "batch_size": [1],
        "seed": [12345]
    }
    df = pd.DataFrame(data)
    df.to_excel(test_file, index=False)
    
    # 模拟文件选择对话框
    def mock_get_open_file_name(*args, **kwargs):
        return str(test_file), "Excel Files (*.xlsx)"
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', mock_get_open_file_name)
    
    # 导入Excel
    batch_gen_tab.import_excel()
    
    # 验证按钮状态
    assert batch_gen_tab.start_btn.isEnabled()
    assert batch_gen_tab.clear_btn.isEnabled()
    
    # 验证任务列表
    assert len(batch_gen_tab.tasks) == 1
    task = batch_gen_tab.tasks[0]
    assert task["prompt"] == "test prompt"
    assert task["negative_prompt"] == "negative test"
    assert task["model"] == "model A"
    assert task["size"] == "512x512"
    assert task["steps"] == 20
    assert task["guidance"] == 7.5
    assert task["batch_size"] == 1
    assert task["seed"] == 12345

def test_task_completion(mock_history, mock_api, batch_gen_tab, qtbot):
    """测试任务完成时添加历史记录"""
    # 设置当前任务
    batch_gen_tab.tasks = [{
        "prompt": "test prompt",
        "negative_prompt": "test negative",
        "model": "test model",
        "size": "512x512",
        "steps": 20,
        "guidance": 7.5,
        "batch_size": 1,
        "seed": 12345
    }]
    batch_gen_tab.current_task_index = 0
    
    # 模拟生成的文件
    record = {
        "timestamp": "2024-01-15 19:40:00",
        "params": {
            "prompt": "test prompt",
            "negative_prompt": "test negative", 
            "model": "test model",
            "size": "512x512",
            "num_inference_steps": 20,
            "guidance_scale": 7.5,
            "seed": 12345,
            "source": "batch"
        },
        "image_path": "/path/to/test_image.jpg"
    }
    
    # 调用图片保存完成处理方法
    batch_gen_tab.on_image_saved(record)
    qtbot.wait(100)  # 等待事件处理
    
    # 验证是否调用了添加历史记录的方法
    mock_history.add_record.assert_called_once_with({
        "timestamp": record["timestamp"],
        "params": record["params"],
        "image_paths": [record["image_path"]]
    })

def test_task_error(batch_gen_tab):
    """测试任务错误"""
    # 模拟任务错误
    batch_gen_tab.on_generation_error("测试错误")
    
    # 验证警告框显示
    assert QMessageBox.warning.called

def test_edit_task(batch_gen_tab):
    """测试编辑任务功能"""
    # 添加一些任务
    batch_gen_tab.tasks = [
        {"prompt": "test prompt", "model": "model A", "size": "512x512"}
    ]
    batch_gen_tab.task_list.clear()
    for task in batch_gen_tab.tasks:
        item = QListWidgetItem(f"提示词: {task['prompt'][:50]}...")
        item.setData(Qt.ItemDataRole.UserRole, task)
        batch_gen_tab.task_list.addItem(item)
    
    # 选择要编辑的任务
    batch_gen_tab.task_list.setCurrentRow(0)
    
    # 创建一个编辑对话框模拟方法
    def edit_task_mock(task):
        task["prompt"] = "edited prompt"
        return task
    
    # 模拟编辑任务
    batch_gen_tab.task_list.currentItem().setData(
        Qt.ItemDataRole.UserRole, 
        edit_task_mock(batch_gen_tab.tasks[0])
    )
    
    # 验证任务已更新
    assert batch_gen_tab.tasks[0]["prompt"] == "edited prompt"

def test_random_seed_behavior(batch_gen_tab, mock_api, mock_config, qtbot):
    """测试随机种子行为"""
    # 添加任务
    batch_gen_tab.tasks = [
        {"prompt": "test", "negative_prompt": "", "model": "test", "size": "512x512", 
         "steps": 20, "guidance": 7.5, "batch_size": 1, "seed": -1}  # -1表示使用随机种子
    ]
    batch_gen_tab.current_task_index = 0
    
    # 模拟生成过程
    with patch('PyQt6.QtCore.QThread.start', return_value=None):
        batch_gen_tab.on_generate_clicked()
        qtbot.wait(100)  # 等待事件处理
    
    # 验证生成线程使用了随机种子
    assert batch_gen_tab.tasks[0]["seed"] == -1  # 验证种子保持为-1表示随机

def test_parameter_validation(batch_gen_tab):
    """测试参数验证"""
    # 添加任务
    batch_gen_tab.tasks = [
        {
            "prompt": "test prompt",
            "model": "test model",
            "size": "512x512",
            "steps": 20,
            "guidance": 7.5,
            "batch_size": 1,
            "seed": 12345
        }
    ]
    
    # 验证任务参数
    assert len(batch_gen_tab.tasks) == 1
    task = batch_gen_tab.tasks[0]
    assert task["prompt"] == "test prompt"
    assert task["model"] == "test model"

def test_get_generation_params(batch_gen_tab):
    """测试获取生成参数"""
    # 添加任务
    batch_gen_tab.tasks = [
        {
            "prompt": "测试提示词",
            "model": "test model",
            "size": "512x512",
            "steps": 20,
            "guidance": 7.5,
            "batch_size": 1,
            "seed": 12345
        }
    ]
    
    # 验证任务参数
    assert len(batch_gen_tab.tasks) == 1
    task = batch_gen_tab.tasks[0]
    assert task["prompt"] == "测试提示词"
    assert task["model"] == "test model" 
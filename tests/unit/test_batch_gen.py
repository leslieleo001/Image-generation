import os
from unittest.mock import MagicMock, patch
import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtTest import QSignalSpy
from src.ui.batch_gen import BatchGenTab
from src.utils import APIManager, ConfigManager

# Mock QMessageBox
QMessageBox.information = MagicMock()
QMessageBox.warning = MagicMock()
QMessageBox.question = MagicMock()

class MockGenerationTask:
    def __init__(self, prompt, model, size):
        self.prompt = prompt
        self.model = model
        self.size = size
        self.status = "等待中"
        self.result_path = None

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
    api = MagicMock()
    api.is_configured = MagicMock()
    api.is_configured.return_value = True
    return api

@pytest.fixture
def mock_config():
    """创建配置管理器mock"""
    config = MagicMock()
    config.get = lambda key, default=None: {
        "model": "模型A",
        "size": "512x512",
        "steps": 20,
        "guidance": 7.5,
        "seed": 12345,
        "models": ["模型A", "模型B"],
        "sizes": ["512x512", "1024x1024"]
    }.get(key, default)
    return config

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
def batch_gen_tab(qtbot, mock_api, mock_config):
    """创建批量生成标签页"""
    tab = BatchGenTab(mock_api, mock_config)
    qtbot.addWidget(tab)
    return tab

@pytest.fixture
def sample_tasks():
    """创建测试任务"""
    return [
        MockGenerationTask(prompt="测试1", model="模型A", size="512x512"),
        MockGenerationTask(prompt="测试2", model="模型B", size="1024x1024")
    ]

def test_init(batch_gen_tab, mock_api, mock_config):
    """测试初始化"""
    assert batch_gen_tab.api == mock_api
    assert batch_gen_tab.config == mock_config
    assert batch_gen_tab.tasks == []
    assert not batch_gen_tab.start_btn.isEnabled()
    assert not batch_gen_tab.pause_btn.isEnabled()
    assert not batch_gen_tab.resume_btn.isEnabled()
    assert not batch_gen_tab.clear_btn.isEnabled()
    assert not batch_gen_tab.export_btn.isEnabled()

def test_import_excel_success(batch_gen_tab, mock_api, mock_config, tmp_path):
    """测试导入Excel成功"""
    # 创建测试Excel文件
    test_file = tmp_path / "test.xlsx"
    test_file.write_text("")
    
    # 模拟文件选择对话框
    batch_gen_tab.get_open_file_name = lambda: (str(test_file), "")
    
    # 导入Excel
    batch_gen_tab.import_excel()
    
    # 验证按钮状态
    assert batch_gen_tab.export_btn.isEnabled()

def test_import_excel_cancel(batch_gen_tab):
    """测试取消导入Excel"""
    # 模拟用户取消选择文件
    batch_gen_tab.get_open_file_name = lambda: ("", "")
    
    # 导入Excel
    batch_gen_tab.import_excel()
    
    # 验证任务列表未改变
    assert len(batch_gen_tab.tasks) == 0

def test_import_excel_error(batch_gen_tab, mock_api, mock_config, tmp_path):
    """测试导入Excel出错"""
    # 创建测试Excel文件
    test_file = tmp_path / "test.xlsx"
    test_file.write_text("")
    
    # 模拟文件选择对话框
    batch_gen_tab.get_open_file_name = lambda: (str(test_file), "")
    
    # 模拟读取任务出错
    def mock_read_tasks(*args):
        raise Exception("读取错误")
    batch_gen_tab.read_tasks = mock_read_tasks
    
    # 导入Excel
    batch_gen_tab.import_excel()
    
    # 验证任务列表未改变
    assert len(batch_gen_tab.tasks) == 0

def test_task_list_operations(batch_gen_tab, sample_tasks):
    """测试任务列表操作"""
    # 添加任务
    batch_gen_tab.tasks.extend(sample_tasks)
    assert len(batch_gen_tab.tasks) == 2
    
    # 清空任务
    batch_gen_tab.clear_tasks()
    assert len(batch_gen_tab.tasks) == 0
    assert not batch_gen_tab.export_btn.isEnabled()

def test_task_completion(batch_gen_tab, sample_tasks):
    """测试任务完成"""
    # 添加任务
    batch_gen_tab.tasks.extend(sample_tasks)
    
    # 模拟任务完成
    batch_gen_tab.on_task_complete()
    
    # 验证消息框显示
    assert QMessageBox.information.called

def test_task_error(batch_gen_tab, sample_tasks):
    """测试任务错误"""
    # 添加任务
    batch_gen_tab.tasks.extend(sample_tasks)
    
    # 模拟任务错误
    batch_gen_tab.on_task_error("测试错误")
    
    # 验证警告框显示
    assert QMessageBox.warning.called

def test_edit_task(batch_gen_tab, sample_tasks):
    """测试编辑任务"""
    # 添加任务
    batch_gen_tab.tasks.extend(sample_tasks)
    
    # 编辑第一个任务
    task = batch_gen_tab.tasks[0]
    new_prompt = "新提示词"
    new_model = "模型B"
    new_size = "1024x1024"
    
    # 模拟对话框输入
    batch_gen_tab.get_task_input = lambda *args: (new_prompt, new_model, new_size)
    
    # 编辑任务
    batch_gen_tab.edit_task(task)
    
    # 验证任务属性已更新
    assert task.prompt == new_prompt
    assert task.model == new_model
    assert task.size == new_size

def test_random_seed_behavior(batch_gen_tab):
    """测试随机种子行为"""
    # 测试初始状态
    assert batch_gen_tab.random_seed_check.isChecked()
    assert not batch_gen_tab.seed_input.isEnabled()
    
    # 测试取消选中
    batch_gen_tab.random_seed_check.setChecked(False)
    assert batch_gen_tab.seed_input.isEnabled()

def test_parameter_validation(batch_gen_tab):
    """测试参数验证"""
    # 测试无效种子值
    batch_gen_tab.random_seed_check.setChecked(False)
    batch_gen_tab.seed_input.setText("0")  # 小于最小值
    assert not batch_gen_tab.validate_parameters()
    
    batch_gen_tab.random_seed_check.setChecked(False)
    batch_gen_tab.seed_input.setText("9999999999")  # 大于最大值
    assert not batch_gen_tab.validate_parameters()
    
    batch_gen_tab.random_seed_check.setChecked(False)
    batch_gen_tab.seed_input.setText("abc")  # 非数字
    assert not batch_gen_tab.validate_parameters()
    
    batch_gen_tab.random_seed_check.setChecked(False)
    batch_gen_tab.seed_input.setText("")  # 空值
    assert not batch_gen_tab.validate_parameters()

    # 测试有效种子值
    batch_gen_tab.random_seed_check.setChecked(False)
    batch_gen_tab.seed_input.setText("1")  # 最小值
    assert batch_gen_tab.validate_parameters()
    
    batch_gen_tab.random_seed_check.setChecked(False)
    batch_gen_tab.seed_input.setText("9999999998")  # 最大值
    assert batch_gen_tab.validate_parameters()
    
    batch_gen_tab.random_seed_check.setChecked(False)
    batch_gen_tab.seed_input.setText("12345")  # 正常值
    assert batch_gen_tab.validate_parameters()

    # 测试随机种子模式
    batch_gen_tab.random_seed_check.setChecked(True)
    assert batch_gen_tab.validate_parameters()  # 随机种子模式下总是有效

def test_get_generation_params(batch_gen_tab):
    """测试获取生成参数"""
    # 设置输入值
    batch_gen_tab.prompt_input.setPlainText("测试提示词")
    batch_gen_tab.model_combo.setCurrentText("模型A")
    batch_gen_tab.size_combo.setCurrentText("512x512")
    batch_gen_tab.steps_spin.setValue(20)
    batch_gen_tab.guidance_spin.setValue(7.5)
    batch_gen_tab.random_seed_check.setChecked(False)
    batch_gen_tab.seed_input.setText("12345")
    
    # 获取参数
    params = batch_gen_tab.get_generation_params()
    
    # 验证参数
    assert params["prompt"] == "测试提示词"
    assert params["model"] == "模型A"
    assert params["size"] == "512x512"
    assert params["steps"] == 20
    assert params["guidance"] == 7.5
    assert params["seed"] == 12345

def test_sort_tasks_by_prompt(batch_gen_tab, sample_tasks):
    """测试按提示词排序"""
    # 添加任务
    batch_gen_tab.tasks.extend(sample_tasks)
    
    # 排序前的顺序
    assert batch_gen_tab.tasks[0].prompt == "测试1"
    assert batch_gen_tab.tasks[1].prompt == "测试2"
    
    # 反转任务列表
    batch_gen_tab.tasks.reverse()
    
    # 按提示词排序
    batch_gen_tab.sort_tasks_by_prompt()
    
    # 验证排序后的顺序
    assert batch_gen_tab.tasks[0].prompt == "测试1"
    assert batch_gen_tab.tasks[1].prompt == "测试2"

def test_sort_tasks_by_status(batch_gen_tab, sample_tasks):
    """测试按状态排序"""
    # 添加任务
    batch_gen_tab.tasks.extend(sample_tasks)
    
    # 设置不同的状态
    batch_gen_tab.tasks[0].status = "完成"
    batch_gen_tab.tasks[1].status = "等待中"
    
    # 按状态排序
    batch_gen_tab.sort_tasks_by_status()
    
    # 验证排序后的顺序
    assert batch_gen_tab.tasks[0].status == "等待中"
    assert batch_gen_tab.tasks[1].status == "完成"

def test_sort_tasks_empty_list(batch_gen_tab):
    """测试空列表排序"""
    # 确保任务列表为空
    assert len(batch_gen_tab.tasks) == 0
    
    # 尝试排序
    batch_gen_tab.sort_tasks_by_prompt()
    batch_gen_tab.sort_tasks_by_status()
    
    # 验证没有错误发生
    assert len(batch_gen_tab.tasks) == 0

def test_ui_initialization(batch_gen_tab):
    """测试UI初始化"""
    # 验证按钮初始状态
    assert not batch_gen_tab.start_btn.isEnabled()
    assert not batch_gen_tab.pause_btn.isEnabled()
    assert not batch_gen_tab.resume_btn.isEnabled()
    assert not batch_gen_tab.clear_btn.isEnabled()
    assert not batch_gen_tab.export_btn.isEnabled()
    
    # 验证输入控件初始状态
    assert batch_gen_tab.random_seed_check.isChecked()
    assert not batch_gen_tab.seed_input.isEnabled()

def test_export_excel_button_enabled(batch_gen_tab, sample_tasks):
    """测试导出Excel按钮状态"""
    # 初始状态
    assert not batch_gen_tab.export_btn.isEnabled()
    
    # 添加任务后
    batch_gen_tab.tasks.extend(sample_tasks)
    assert batch_gen_tab.export_btn.isEnabled()
    
    # 清空任务后
    batch_gen_tab.clear_tasks()
    assert not batch_gen_tab.export_btn.isEnabled()

def test_export_excel_error(batch_gen_tab, sample_tasks, tmp_path):
    """测试导出Excel错误处理"""
    # 创建测试文件
    test_file = tmp_path / "test.xlsx"
    
    # 模拟文件选择对话框
    batch_gen_tab.get_save_file_name = lambda: (str(test_file), "")
    
    # 模拟导出错误
    def mock_export(*args):
        raise Exception("导出错误")
    batch_gen_tab.export_tasks = mock_export
    
    # 添加任务
    batch_gen_tab.tasks.extend(sample_tasks)
    
    # 尝试导出
    batch_gen_tab.export_excel()
    
    # 验证错误处理
    assert QMessageBox.warning.called 
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox, QInputDialog, QPushButton, QDialog, QLineEdit, QComboBox, QDialogButtonBox
from src.ui.batch_gen import BatchGenTab
from src.utils.excel_handler import GenerationTask, ExcelHandler
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

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
def mock_api():
    """创建模拟API"""
    api = MagicMock()
    api.is_configured.return_value = True
    api.generate_image.return_value = {"image_path": "test/image.png"}
    return api

@pytest.fixture
def mock_config():
    """创建模拟配置"""
    config = MagicMock()
    config.get.return_value = ["模型A", "模型B", "模型C"]  # 为所有get调用返回相同的列表
    return config

@pytest.fixture
def batch_gen_tab(app, mock_api, mock_config):
    """创建批量生成界面"""
    return BatchGenTab(mock_api, mock_config)

@pytest.fixture
def sample_tasks():
    """创建测试任务"""
    return [
        GenerationTask(prompt="测试1"),
        GenerationTask(prompt="测试2")
    ]

def test_init(batch_gen_tab):
    """测试初始化"""
    assert batch_gen_tab.api is not None
    assert batch_gen_tab.config is not None
    assert batch_gen_tab.task_queue is not None
    assert len(batch_gen_tab.tasks) == 0
    
    # 检查按钮状态
    assert not batch_gen_tab.start_btn.isEnabled()
    assert not batch_gen_tab.pause_btn.isEnabled()
    assert not batch_gen_tab.resume_btn.isEnabled()
    assert not batch_gen_tab.clear_btn.isEnabled()
    assert not batch_gen_tab.export_btn.isEnabled()

@patch("PyQt6.QtWidgets.QFileDialog.getOpenFileName")
def test_import_excel_success(mock_dialog, batch_gen_tab):
    """测试成功导入Excel"""
    # 模拟文件选择
    mock_dialog.return_value = ("test.xlsx", "Excel Files (*.xlsx)")
    
    # 模拟ExcelHandler
    with patch("src.utils.excel_handler.ExcelHandler.read_tasks") as mock_read:
        mock_read.return_value = [
            GenerationTask(prompt="测试1", model="模型A", size="512x512"),
            GenerationTask(prompt="测试2", model="模型B", size="1024x1024")
        ]
        
        # 执行导入
        batch_gen_tab.import_excel()
        
        # 验证调用
        mock_dialog.assert_called_once()
        mock_read.assert_called_once()
        
        # 验证任务导入
        assert len(batch_gen_tab.tasks) == 2
        assert batch_gen_tab.tasks[0].prompt == "测试1"
        assert batch_gen_tab.tasks[0].model == "模型A"
        assert batch_gen_tab.tasks[0].size == "512x512"
        assert batch_gen_tab.tasks[0].status == "等待中"
        
        assert batch_gen_tab.tasks[1].prompt == "测试2"
        assert batch_gen_tab.tasks[1].model == "模型B"
        assert batch_gen_tab.tasks[1].size == "1024x1024"
        assert batch_gen_tab.tasks[1].status == "等待中"
        
        # 验证按钮状态
        assert batch_gen_tab.start_btn.isEnabled()
        assert batch_gen_tab.clear_btn.isEnabled()
        assert batch_gen_tab.export_btn.isEnabled()

@patch("PyQt6.QtWidgets.QFileDialog.getOpenFileName")
def test_import_excel_error(mock_dialog, batch_gen_tab):
    """测试导入Excel失败"""
    # 模拟文件选择
    mock_dialog.return_value = ("test.xlsx", "")
    
    # 模拟ExcelHandler抛出异常
    with patch("src.utils.excel_handler.ExcelHandler.read_tasks") as mock_read:
        mock_read.side_effect = Exception("读取失败")
        with patch("PyQt6.QtWidgets.QMessageBox.critical") as mock_message:
            batch_gen_tab.import_excel()
            mock_message.assert_called_once()

def test_task_list_operations(batch_gen_tab):
    """测试任务列表的基本操作"""
    # 初始状态下任务列表为空
    assert len(batch_gen_tab.tasks) == 0
    
    # 添加一个任务
    task = GenerationTask(prompt="测试提示词", model="模型A", size="512x512")
    batch_gen_tab.tasks.append(task)
    assert len(batch_gen_tab.tasks) == 1
    assert batch_gen_tab.tasks[0].prompt == "测试提示词"
    
    # 清空任务
    batch_gen_tab.tasks.clear()
    assert len(batch_gen_tab.tasks) == 0

def test_export_excel_button_enabled(batch_gen_tab):
    """测试导出按钮的启用状态"""
    # 初始状态下应该禁用
    assert not batch_gen_tab.export_btn.isEnabled()
    
    # 添加一个任务
    task = GenerationTask(prompt="测试提示词", model="模型A", size="512x512")
    batch_gen_tab.tasks.append(task)
    batch_gen_tab.update_table()  # 更新表格以触发按钮状态更新
    
    # 有任务时应该启用
    assert len(batch_gen_tab.tasks) > 0
    assert batch_gen_tab.export_btn.isEnabled()
    
    # 清空任务
    batch_gen_tab.tasks.clear()
    batch_gen_tab.update_table()  # 更新表格以触发按钮状态更新
    
    # 无任务时应该禁用
    assert len(batch_gen_tab.tasks) == 0
    assert not batch_gen_tab.export_btn.isEnabled()

def test_export_excel_dialog(batch_gen_tab):
    """测试导出Excel对话框"""
    # 创建测试任务
    tasks = [
        GenerationTask(prompt="测试1", model="模型A", size="512x512"),
        GenerationTask(prompt="测试2", model="模型B", size="1024x1024")
    ]
    batch_gen_tab.tasks = tasks
    
    # 模拟文件对话框
    with patch("PyQt6.QtWidgets.QFileDialog.getSaveFileName") as mock_dialog:
        # 模拟用户取消
        mock_dialog.return_value = ("", "")
        batch_gen_tab.export_excel()
        mock_dialog.assert_called_once()
        
        # 验证任务列表未改变
        assert len(batch_gen_tab.tasks) == 2
        assert batch_gen_tab.tasks[0].prompt == "测试1"
        assert batch_gen_tab.tasks[1].prompt == "测试2"
        
        # 模拟用户选择文件
        mock_dialog.reset_mock()
        mock_dialog.return_value = ("test.xlsx", "Excel Files (*.xlsx)")
        
        with patch("src.utils.excel_handler.ExcelHandler.export_results") as mock_export:
            batch_gen_tab.export_excel()
            mock_dialog.assert_called_once()
            mock_export.assert_called_once_with(batch_gen_tab.tasks, "test.xlsx")

def test_export_excel_error_handling(batch_gen_tab):
    """测试导出Excel错误处理"""
    # 创建测试任务
    tasks = [
        GenerationTask(prompt="测试1", model="模型A", size="512x512"),
        GenerationTask(prompt="测试2", model="模型B", size="1024x1024")
    ]
    batch_gen_tab.tasks = tasks
    
    with patch("PyQt6.QtWidgets.QFileDialog.getSaveFileName") as mock_dialog:
        with patch("src.utils.excel_handler.ExcelHandler.export_results") as mock_export:
            with patch("PyQt6.QtWidgets.QMessageBox.critical") as mock_error:
                # 设置模拟返回值
                mock_dialog.return_value = ("test.xlsx", "")
                mock_export.side_effect = Exception("导出错误")
                
                # 执行导出
                batch_gen_tab.export_excel()
                
                # 验证调用
                mock_dialog.assert_called_once()
                mock_export.assert_called_once()
                mock_error.assert_called_once()

def test_start_generation_no_api_key(batch_gen_tab):
    """测试无API密钥时开始生成"""
    batch_gen_tab.api.is_configured.return_value = False
    # 创建测试任务
    tasks = [
        GenerationTask(prompt="测试1", model="模型A", size="512x512"),
        GenerationTask(prompt="测试2", model="模型B", size="1024x1024")
    ]
    batch_gen_tab.tasks = tasks
    
    with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_message:
        batch_gen_tab.start_generation()
        mock_message.assert_called_once()

def test_pause_resume_generation(batch_gen_tab):
    """测试暂停和恢复生成"""
    # 测试暂停
    batch_gen_tab.pause_generation()
    assert not batch_gen_tab.pause_btn.isEnabled()
    assert batch_gen_tab.resume_btn.isEnabled()
    
    # 测试恢复
    batch_gen_tab.resume_generation()
    assert batch_gen_tab.pause_btn.isEnabled()
    assert not batch_gen_tab.resume_btn.isEnabled()

def test_clear_tasks(batch_gen_tab):
    """测试清空任务"""
    # 创建测试任务
    tasks = [
        GenerationTask(prompt="测试1", model="模型A", size="512x512"),
        GenerationTask(prompt="测试2", model="模型B", size="1024x1024")
    ]
    batch_gen_tab.tasks = tasks
    batch_gen_tab.clear_tasks()
    
    # 验证状态
    assert len(batch_gen_tab.tasks) == 0
    assert batch_gen_tab.progress_bar.value() == 0
    assert not batch_gen_tab.start_btn.isEnabled()
    assert not batch_gen_tab.pause_btn.isEnabled()
    assert not batch_gen_tab.resume_btn.isEnabled()
    assert not batch_gen_tab.clear_btn.isEnabled()
    assert not batch_gen_tab.export_btn.isEnabled()
    assert batch_gen_tab.import_btn.isEnabled()

def test_update_progress(batch_gen_tab):
    """测试更新进度"""
    batch_gen_tab.update_progress(5, 10)
    assert batch_gen_tab.progress_bar.value() == 50

def test_on_task_complete(batch_gen_tab):
    """测试任务完成回调"""
    # 创建测试任务
    tasks = [
        GenerationTask(prompt="测试1", model="模型A", size="512x512"),
        GenerationTask(prompt="测试2", model="模型B", size="1024x1024")
    ]
    batch_gen_tab.tasks = tasks
    batch_gen_tab.tasks[0].status = "完成"
    batch_gen_tab.tasks[1].status = "完成"
    
    with patch("PyQt6.QtWidgets.QMessageBox.information") as mock_message:
        batch_gen_tab.on_task_complete(batch_gen_tab.tasks[1])
        mock_message.assert_called_once()
        
    # 验证按钮状态
    assert not batch_gen_tab.start_btn.isEnabled()
    assert not batch_gen_tab.pause_btn.isEnabled()
    assert not batch_gen_tab.resume_btn.isEnabled()
    assert batch_gen_tab.import_btn.isEnabled()

def test_on_task_error(batch_gen_tab):
    """测试任务错误回调"""
    # 创建测试任务
    tasks = [
        GenerationTask(prompt="测试1", model="模型A", size="512x512"),
        GenerationTask(prompt="测试2", model="模型B", size="1024x1024")
    ]
    batch_gen_tab.tasks = tasks
    
    with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_message:
        batch_gen_tab.on_task_error(batch_gen_tab.tasks[0], "测试错误")
        mock_message.assert_called_once()

@pytest.mark.qt
def test_edit_task(batch_gen_tab):
    """测试编辑任务功能"""
    # 添加一个测试任务
    task = GenerationTask(prompt="测试提示词", model="模型A", size="512x512")
    batch_gen_tab.tasks.append(task)
    
    # 模拟编辑对话框
    with patch.object(QDialog, 'exec', return_value=QDialog.DialogCode.Accepted):
        with patch.object(QLineEdit, 'text', return_value="新提示词"):
            with patch.object(QComboBox, 'currentText', side_effect=["模型B", "1024x1024"]):
                # 执行编辑
                batch_gen_tab.edit_task(0)
                
                # 验证任务是否被更新
                assert batch_gen_tab.tasks[0].prompt == "新提示词"
                assert batch_gen_tab.tasks[0].model == "模型B"
                assert batch_gen_tab.tasks[0].size == "1024x1024"
                assert batch_gen_tab.tasks[0].status == "等待中"
                assert batch_gen_tab.tasks[0].result_path is None

def test_edit_task_validation(batch_gen_tab):
    """测试编辑任务输入验证"""
    # 添加测试任务
    task = GenerationTask(prompt="测试提示词", model="模型A", size="512x512")
    batch_gen_tab.tasks.append(task)
    
    # 模拟编辑对话框
    with patch.object(QDialog, 'exec', return_value=QDialog.DialogCode.Accepted):
        with patch.object(QLineEdit, 'text', return_value=""):
            with patch.object(QMessageBox, 'warning') as mock_warning:
                # 执行编辑
                batch_gen_tab.edit_task(0)
                
                # 验证警告是否显示
                mock_warning.assert_called_once()
                
                # 验证任务未被更新
                assert batch_gen_tab.tasks[0].prompt == "测试提示词"
                assert batch_gen_tab.tasks[0].model == "模型A"
                assert batch_gen_tab.tasks[0].size == "512x512"

def test_edit_task_cancel(batch_gen_tab):
    """测试取消编辑任务"""
    # 添加测试任务
    task = GenerationTask(prompt="测试提示词", model="模型A", size="512x512")
    batch_gen_tab.tasks.append(task)
    
    # 模拟编辑对话框
    with patch.object(QDialog, 'exec', return_value=QDialog.DialogCode.Rejected):
        # 执行编辑
        batch_gen_tab.edit_task(0)
        
        # 验证任务未被更新
        assert batch_gen_tab.tasks[0].prompt == "测试提示词"
        assert batch_gen_tab.tasks[0].model == "模型A"
        assert batch_gen_tab.tasks[0].size == "512x512"

def test_edit_task_invalid_index(batch_gen_tab):
    """测试编辑无效索引的任务"""
    # 尝试编辑不存在的任务
    batch_gen_tab.edit_task(-1)  # 负数索引
    batch_gen_tab.edit_task(0)   # 空列表的索引
    
    # 添加一个任务
    task = GenerationTask(prompt="测试提示词", model="模型A", size="512x512")
    batch_gen_tab.tasks.append(task)
    
    # 尝试编辑超出范围的索引
    batch_gen_tab.edit_task(1)  # 超出列表长度的索引

def test_export_excel_validation(batch_gen_tab):
    """测试导出Excel的输入验证"""
    # 测试无任务时的情况
    with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warning:
        batch_gen_tab.export_excel()
        mock_warning.assert_called_once()

def test_export_excel_success(batch_gen_tab):
    """测试成功导出Excel"""
    # 创建测试任务
    tasks = [
        GenerationTask(prompt="测试1", model="模型A", size="512x512"),
        GenerationTask(prompt="测试2", model="模型B", size="1024x1024")
    ]
    batch_gen_tab.tasks = tasks
    
    with patch("PyQt6.QtWidgets.QFileDialog.getSaveFileName") as mock_dialog:
        with patch("src.utils.excel_handler.ExcelHandler.export_results") as mock_export:
            with patch("PyQt6.QtWidgets.QMessageBox.information") as mock_info:
                # 设置模拟返回值
                mock_dialog.return_value = ("test.xlsx", "")
                
                # 执行导出
                batch_gen_tab.export_excel()
                
                # 验证调用
                mock_dialog.assert_called_once()
                mock_export.assert_called_once()
                mock_info.assert_called_once()

def test_export_excel_cancel(batch_gen_tab):
    """测试取消导出Excel"""
    # 创建测试任务
    tasks = [
        GenerationTask(prompt="测试1", model="模型A", size="512x512"),
        GenerationTask(prompt="测试2", model="模型B", size="1024x1024")
    ]
    batch_gen_tab.tasks = tasks
    
    with patch("PyQt6.QtWidgets.QFileDialog.getSaveFileName") as mock_dialog:
        # 模拟用户取消
        mock_dialog.return_value = ("", "")
        
        # 执行导出
        batch_gen_tab.export_excel()
        
        # 验证调用
        mock_dialog.assert_called_once()

def test_export_excel_error(batch_gen_tab):
    """测试导出Excel出错"""
    # 创建测试任务
    tasks = [
        GenerationTask(prompt="测试1", model="模型A", size="512x512"),
        GenerationTask(prompt="测试2", model="模型B", size="1024x1024")
    ]
    batch_gen_tab.tasks = tasks
    
    with patch("PyQt6.QtWidgets.QFileDialog.getSaveFileName") as mock_dialog:
        with patch("src.utils.excel_handler.ExcelHandler.export_results") as mock_export:
            with patch("PyQt6.QtWidgets.QMessageBox.critical") as mock_error:
                # 设置模拟返回值
                mock_dialog.return_value = ("test.xlsx", "")
                mock_export.side_effect = Exception("导出错误")
                
                # 执行导出
                batch_gen_tab.export_excel()
                
                # 验证调用
                mock_dialog.assert_called_once()
                mock_export.assert_called_once()
                mock_error.assert_called_once()

def test_sort_tasks_by_prompt(batch_gen_tab):
    """测试按提示词排序"""
    # 添加测试任务
    tasks = [
        GenerationTask(prompt="测试C", model="模型A", size="512x512"),
        GenerationTask(prompt="测试A", model="模型B", size="1024x1024"),
        GenerationTask(prompt="测试B", model="模型C", size="768x768")
    ]
    batch_gen_tab.tasks = tasks
    batch_gen_tab.update_table()
    
    # 执行排序
    batch_gen_tab.sort_tasks_by_prompt()
    
    # 验证排序结果
    assert batch_gen_tab.tasks[0].prompt == "测试A"
    assert batch_gen_tab.tasks[1].prompt == "测试B"
    assert batch_gen_tab.tasks[2].prompt == "测试C"
    
def test_sort_tasks_by_status(batch_gen_tab):
    """测试按状态排序"""
    # 添加测试任务
    tasks = [
        GenerationTask(prompt="测试1", model="模型A", size="512x512"),
        GenerationTask(prompt="测试2", model="模型B", size="1024x1024"),
        GenerationTask(prompt="测试3", model="模型C", size="768x768"),
        GenerationTask(prompt="测试4", model="模型D", size="512x512")
    ]
    tasks[0].status = "完成"
    tasks[1].status = "等待中"
    tasks[2].status = "处理中"
    tasks[3].status = "失败"
    batch_gen_tab.tasks = tasks
    batch_gen_tab.update_table()
    
    # 执行排序
    batch_gen_tab.sort_tasks_by_status()
    
    # 验证排序结果
    assert batch_gen_tab.tasks[0].status == "处理中"
    assert batch_gen_tab.tasks[1].status == "等待中"
    assert batch_gen_tab.tasks[2].status == "完成"
    assert batch_gen_tab.tasks[3].status == "失败"
    
def test_sort_tasks_empty_list(batch_gen_tab):
    """测试空任务列表排序"""
    # 执行排序
    batch_gen_tab.sort_tasks_by_prompt()
    batch_gen_tab.sort_tasks_by_status()
    
    # 验证结果
    assert len(batch_gen_tab.tasks) == 0 
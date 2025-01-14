import pytest
from unittest.mock import MagicMock, patch
from queue import Queue
from threading import Event
import time
from src.utils.task_queue import TaskQueue
from src.utils.excel_handler import GenerationTask
from src.utils.api_client import SiliconFlowAPI

@pytest.fixture
def mock_api():
    """创建模拟API"""
    api = MagicMock(spec=SiliconFlowAPI)
    api.generate_image.return_value = {"image_path": "test.png"}
    return api

@pytest.fixture
def task_queue(mock_api):
    """创建任务队列"""
    queue = TaskQueue(mock_api)
    yield queue
    queue.stop()  # 确保测试后停止队列

@pytest.fixture
def sample_tasks():
    """创建示例任务"""
    return [
        GenerationTask(prompt="测试1", model="模型A", size="512x512"),
        GenerationTask(prompt="测试2", model="模型B", size="1024x1024")
    ]

def test_init(task_queue):
    """测试初始化"""
    assert task_queue.api is not None
    assert isinstance(task_queue.queue, Queue)
    assert isinstance(task_queue.tasks, list)
    assert task_queue.current_task is None
    assert task_queue.worker_thread is None
    assert isinstance(task_queue.pause_event, Event)
    assert isinstance(task_queue.stop_event, Event)

def test_add_tasks(task_queue, sample_tasks):
    """测试添加任务"""
    # 设置进度回调
    progress_mock = MagicMock()
    task_queue.on_progress_update = progress_mock
    
    # 添加任务
    task_queue.add_tasks(sample_tasks)
    
    # 验证任务添加
    assert len(task_queue.tasks) == 2
    assert task_queue.tasks[0].prompt == "测试1"
    assert task_queue.tasks[1].prompt == "测试2"
    
    # 验证进度回调
    progress_mock.assert_called_once_with(0, 2)

def test_clear_tasks(task_queue, sample_tasks):
    """测试清空任务"""
    # 添加任务并启动队列
    task_queue.add_tasks(sample_tasks)
    task_queue.start()
    time.sleep(0.2)  # 等待线程启动
    
    # 设置进度回调
    progress_mock = MagicMock()
    task_queue.on_progress_update = progress_mock
    
    # 清空任务
    task_queue.clear_tasks()
    
    # 验证任务清空
    assert len(task_queue.tasks) == 0
    assert task_queue.queue.empty()
    assert not task_queue.worker_thread
    
    # 验证进度回调
    progress_mock.assert_called_once_with(0, 0)

def test_start_stop(task_queue, sample_tasks):
    """测试启动和停止"""
    # 添加任务
    task_queue.add_tasks(sample_tasks)
    
    # 启动队列
    task_queue.start()
    time.sleep(0.2)  # 等待线程启动
    
    # 验证线程状态
    assert task_queue.worker_thread is not None
    assert task_queue.worker_thread.is_alive()
    
    # 停止队列
    task_queue.stop()
    time.sleep(0.2)  # 等待线程停止
    
    # 验证线程状态
    assert task_queue.worker_thread is None
    assert task_queue.current_task is None

def test_pause_resume(task_queue, sample_tasks):
    """测试暂停和恢复"""
    # 添加任务
    task_queue.add_tasks(sample_tasks)
    
    # 启动队列
    task_queue.start()
    time.sleep(0.2)  # 等待线程启动
    
    # 暂停队列
    task_queue.pause()
    assert not task_queue.pause_event.is_set()
    
    # 恢复队列
    task_queue.resume()
    assert task_queue.pause_event.is_set()

def test_task_processing(task_queue, sample_tasks):
    """测试任务处理"""
    # 设置回调
    complete_mock = MagicMock()
    progress_mock = MagicMock()
    task_queue.on_task_complete = complete_mock
    task_queue.on_progress_update = progress_mock
    
    # 添加任务并启动
    task_queue.add_tasks(sample_tasks)
    task_queue.start()
    
    # 等待任务完成
    time.sleep(0.5)
    
    # 验证任务状态
    assert all(task.status == "完成" for task in task_queue.tasks)
    assert all(task.result == {"image_path": "test.png"} for task in task_queue.tasks)
    
    # 验证回调
    assert complete_mock.call_count == 2
    progress_mock.assert_called_with(2, 2)

def test_task_error(task_queue, sample_tasks, mock_api):
    """测试任务错误处理"""
    # 设置API抛出异常
    mock_api.generate_image.side_effect = Exception("API错误")
    
    # 设置回调
    error_mock = MagicMock()
    progress_mock = MagicMock()
    task_queue.on_task_error = error_mock
    task_queue.on_progress_update = progress_mock
    
    # 添加任务并启动
    task_queue.add_tasks(sample_tasks)
    task_queue.start()
    
    # 等待任务完成
    time.sleep(0.5)
    
    # 验证任务状态
    assert all(task.status == "失败" for task in task_queue.tasks)
    assert all(task.error == "API错误" for task in task_queue.tasks)
    
    # 验证回调
    assert error_mock.call_count == 2
    progress_mock.assert_called_with(2, 2) 
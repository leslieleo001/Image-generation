from typing import List, Optional, Callable
from queue import Queue, Empty
from threading import Thread, Event, Lock
from .excel_handler import GenerationTask
from .api_client import SiliconFlowAPI
import time
import logging

class TaskQueue:
    """任务队列管理类"""
    
    def __init__(self, api: SiliconFlowAPI):
        self.api = api
        self.queue = Queue()
        self.tasks: List[GenerationTask] = []
        self._current_task: Optional[GenerationTask] = None
        self._current_task_lock = Lock()
        
        # 线程控制
        self.worker_thread: Optional[Thread] = None
        self.pause_event = Event()
        self.stop_event = Event()
        
        # 回调函数
        self.on_task_complete: Optional[Callable] = None
        self.on_task_error: Optional[Callable] = None
        self.on_progress_update: Optional[Callable] = None
        
    @property
    def current_task(self) -> Optional[GenerationTask]:
        """获取当前任务"""
        with self._current_task_lock:
            return self._current_task
            
    @current_task.setter
    def current_task(self, task: Optional[GenerationTask]) -> None:
        """设置当前任务"""
        with self._current_task_lock:
            self._current_task = task
    
    def add_tasks(self, tasks: List[GenerationTask]) -> None:
        """添加任务到队列
        
        Args:
            tasks: 任务列表
        """
        try:
            for task in tasks:
                self.queue.put(task)
                self.tasks.append(task)
            
            # 更新进度
            if self.on_progress_update:
                self.on_progress_update(0, len(self.tasks))
                
        except Exception as e:
            logging.error(f"添加任务失败: {str(e)}")
            raise
    
    def clear_tasks(self) -> None:
        """清空任务队列"""
        try:
            # 停止当前处理
            self.stop()
            
            # 清空队列和任务列表
            while not self.queue.empty():
                self.queue.get()
            self.tasks.clear()
            
            # 更新进度
            if self.on_progress_update:
                self.on_progress_update(0, 0)
                
        except Exception as e:
            logging.error(f"清空任务失败: {str(e)}")
            raise
    
    def start(self) -> None:
        """开始处理任务"""
        if self.worker_thread and self.worker_thread.is_alive():
            return
            
        self.pause_event.set()
        self.stop_event.clear()
        self.worker_thread = Thread(target=self._process_queue)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        # 等待线程启动
        time.sleep(0.1)
    
    def stop(self) -> None:
        """停止处理任务"""
        if not self.worker_thread:
            return
            
        self.stop_event.set()
        self.pause_event.set()  # 确保线程不会卡在暂停状态
        
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        self.worker_thread = None
    
    def pause(self) -> None:
        """暂停处理任务"""
        self.pause_event.clear()
    
    def resume(self) -> None:
        """恢复处理任务"""
        self.pause_event.set()
    
    def _process_queue(self) -> None:
        """处理任务队列"""
        while not self.stop_event.is_set():
            # 等待暂停事件
            if not self.pause_event.wait(timeout=0.1):
                continue
                
            try:
                # 获取任务
                task = self.queue.get(timeout=0.1)
                self.current_task = task
                task.status = "处理中"
                
                try:
                    # 调用API生成图片
                    result = self.api.generate_image(
                        prompt=task.prompt,
                        model=task.model,
                        size=task.size
                    )
                    
                    # 更新任务状态
                    task.status = "完成"
                    task.result = result
                    
                    # 调用完成回调
                    if self.on_task_complete:
                        self.on_task_complete(task)
                        
                except Exception as e:
                    # 更新任务状态
                    task.status = "失败"
                    task.error = str(e)
                    
                    # 调用错误回调
                    if self.on_task_error:
                        self.on_task_error(task)
                    
                    logging.error(f"任务处理失败: {str(e)}")
                    
                finally:
                    # 更新进度
                    completed = sum(1 for t in self.tasks if t.status in ["完成", "失败"])
                    if self.on_progress_update:
                        self.on_progress_update(completed, len(self.tasks))
                    
                    self.current_task = None
                    self.queue.task_done()
                    
            except Empty:
                continue
            except Exception as e:
                logging.error(f"队列处理错误: {str(e)}")
                continue
                
        # 清理状态
        self.current_task = None 
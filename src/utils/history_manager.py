import json
from pathlib import Path
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

class HistoryManager(QObject):
    """历史记录管理器"""
    history_updated = pyqtSignal()  # 历史记录更新信号
    
    def __init__(self, history_file=None):
        super().__init__()
        if history_file is None:
            # 使用配置目录
            config_dir = Path.home() / '.image_generator'
            config_dir.mkdir(parents=True, exist_ok=True)
            self.history_file = config_dir / 'history.json'
        else:
            self.history_file = Path(history_file)
        self.records = []
        self.load_records()
        
    def load_records(self):
        """加载历史记录"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
            else:
                self.records = []
        except Exception as e:
            print(f"加载历史记录失败: {str(e)}")
            self.records = []
            
    def save_records(self):
        """保存历史记录"""
        try:
            # 确保目录存在
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {str(e)}")
            
    def add_record(self, record):
        """添加历史记录"""
        try:
            self.records.insert(0, record)  # 在开头插入新记录
            self.save_records()
            self.history_updated.emit()
        except Exception as e:
            print(f"添加历史记录失败: {str(e)}")
            
    def clear_records(self):
        """清空历史记录"""
        try:
            self.records = []
            self.save_records()
            self.history_updated.emit()
        except Exception as e:
            print(f"清空历史记录失败: {str(e)}")
            
    def get_records(self):
        """获取所有历史记录"""
        return self.records 
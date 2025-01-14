from dataclasses import dataclass

@dataclass
class GenerationTask:
    """生成任务类"""
    prompt: str
    model: str
    size: str
    status: str = "等待中"
    result_path: str = None
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保字符串属性不为 None
        self.prompt = str(self.prompt).strip() if self.prompt else ""
        self.model = str(self.model).strip() if self.model else ""
        self.size = str(self.size).strip() if self.size else ""
        self.status = str(self.status).strip() if self.status else "等待中"
        # result_path 可以为 None 
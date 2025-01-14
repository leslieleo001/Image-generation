from PyQt6.QtCore import QObject, pyqtSignal
from .api_client import SiliconFlowAPI
from .config_manager import ConfigManager

class APIManager(QObject):
    api_status_changed = pyqtSignal(bool)  # 信号：API状态变化
    
    def __init__(self, config: ConfigManager):
        """
        初始化API管理器
        
        Args:
            config: 配置管理器实例
        """
        super().__init__()
        self.config = config
        self._api = None
        self.refresh_api()
    
    def refresh_api(self) -> SiliconFlowAPI:
        """
        刷新API实例，如果API密钥发生变化则创建新实例
        
        Returns:
            SiliconFlowAPI: API客户端实例
        """
        api_key = self.config.get("api.key", "")
        
        # 如果API密钥为空，返回None
        if not api_key:
            self._api = None
            self.api_status_changed.emit(False)
            return None
            
        # 如果API实例不存在或API密钥已更改，创建新实例
        if self._api is None or self._api.api_key != api_key:
            self._api = SiliconFlowAPI(api_key)
            self.api_status_changed.emit(True)
            
        return self._api
    
    @property
    def api(self) -> SiliconFlowAPI:
        """
        获取当前API实例
        
        Returns:
            SiliconFlowAPI: API客户端实例
        """
        return self.refresh_api() 
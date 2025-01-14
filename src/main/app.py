from PyQt6.QtWidgets import QMainWindow, QTabWidget
from src.ui.single_gen import SingleGenTab
from src.ui.batch_gen import BatchGenTab
from src.ui.settings import SettingsTab
from src.utils.config_manager import ConfigManager
from src.utils.api_manager import APIManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI图片生成助手")
        self.resize(1200, 800)
        
        # 初始化配置管理器
        self.config = ConfigManager()
        
        # 初始化API管理器
        self.api_manager = APIManager(self.config)
        
        # 创建标签页
        self.init_tabs()
        
    def init_tabs(self):
        """初始化标签页"""
        # 创建标签页组件
        tabs = QTabWidget()
        
        # 创建各个标签页
        self.single_gen_tab = SingleGenTab(self.config, self.api_manager)
        self.batch_gen_tab = BatchGenTab(self.config, self.api_manager)
        self.settings_tab = SettingsTab(self.config, self.api_manager)
        
        # 连接设置更新信号
        self.settings_tab.settings_updated.connect(self.single_gen_tab.update_defaults)
        self.settings_tab.settings_updated.connect(self.batch_gen_tab.update_defaults)
        
        # 添加标签页
        tabs.addTab(self.single_gen_tab, "手动生成")
        tabs.addTab(self.batch_gen_tab, "批量生成")
        tabs.addTab(self.settings_tab, "设置")
        
        # 设置中心部件
        self.setCentralWidget(tabs) 
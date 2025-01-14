from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt6.QtCore import Qt
from src.ui.single_gen import SingleGenTab
from src.ui.batch_gen import BatchGenTab
from src.ui.settings import SettingsTab
from src.utils.config_manager import ConfigManager
from src.utils.api_manager import APIManager
from src.utils.history_manager import HistoryManager

class HelpTab(QWidget):
    """帮助标签页"""
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # 创建帮助文本
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMarkdown("""
# AI图片生成助手使用说明

## 1. 手动生成
- 输入提示词和负面提示词
- 选择模型和参数
- 点击生成按钮开始生成
- 可以预览和保存生成的图片
- 支持历史记录管理

## 2. 批量生成
- 支持多行提示词输入
- 可以从Excel导入参数
- 支持下载参数模板
- 可以暂停和继续生成
- 支持历史记录管理

## 3. 设置
- 配置API密钥
- 设置默认参数
- 配置输出路径
- 管理命名规则

## 4. 参数说明
- 模型：选择使用的AI模型
- 尺寸：生成图片的尺寸
- 步数：生成的迭代步数（turbo模型固定为4步）
- 引导系数：控制生成图片与提示词的相关度
- 批量大小：一次生成的图片数量
- 种子值：控制生成结果的随机性
- 提示增强：优化提示词以提高生成质量

## 5. 命名规则
支持以下变量：
- {timestamp}: 时间戳
- {date}: 日期
- {time}: 时间
- {prompt}: 提示词
- {model}: 模型名称
- {size}: 图片尺寸
- {seed}: 种子值
- {index}: 序号

## 6. 注意事项
1. 首次使用请先在设置中配置API密钥
2. 建议使用英文提示词以获得更好的效果
3. 负面提示词可以帮助避免不想要的元素
4. 批量生成时建议先下载模板参考格式
5. 生成过程中可以随时暂停和继续
6. 所有生成记录都会保存在历史记录中
""")
        
        layout.addWidget(help_text)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI图片生成助手")
        self.resize(1200, 800)
        
        # 初始化配置管理器
        self.config = ConfigManager()
        
        # 初始化API管理器
        self.api_manager = APIManager(self.config)
        
        # 初始化历史记录管理器
        self.history_manager = HistoryManager()
        
        # 创建标签页
        self.init_tabs()
        
    def init_tabs(self):
        """初始化标签页"""
        # 创建标签页组件
        tabs = QTabWidget()
        
        # 创建各个标签页
        self.single_gen_tab = SingleGenTab(self.config, self.api_manager, self.history_manager)
        self.batch_gen_tab = BatchGenTab(self.api_manager, self.config, self.history_manager)
        self.settings_tab = SettingsTab(self.config, self.api_manager)
        self.help_tab = HelpTab()
        
        # 连接设置更新信号
        self.settings_tab.settings_updated.connect(self.single_gen_tab.update_defaults)
        self.settings_tab.settings_updated.connect(self.batch_gen_tab.update_defaults)
        
        # 添加标签页
        tabs.addTab(self.single_gen_tab, "手动生成")
        tabs.addTab(self.batch_gen_tab, "批量生成")
        tabs.addTab(self.settings_tab, "设置")
        tabs.addTab(self.help_tab, "帮助")
        
        # 设置中心部件
        self.setCentralWidget(tabs) 
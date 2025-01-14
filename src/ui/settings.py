from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                           QPushButton, QGroupBox, QFileDialog, QMessageBox, QHBoxLayout, QSizePolicy, QComboBox, QLabel, QSpinBox, QDoubleSpinBox)
from src.utils.config_manager import ConfigManager
from src.utils.api_client import SiliconFlowAPI, APIError
from src.utils.api_manager import APIManager
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIntValidator

class APITestThread(QThread):
    """API测试线程"""
    success = pyqtSignal()  # 测试成功信号
    error = pyqtSignal(str)  # 测试失败信号
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        
    def run(self):
        try:
            api = SiliconFlowAPI(self.api_key)
            if api.validate_api_key():
                self.success.emit()
            else:
                self.error.emit("API密钥无效")
        except APIError as e:
            self.error.emit(f"API测试失败: {e.message}")
        except Exception as e:
            self.error.emit(f"发生未知错误: {str(e)}")

class SettingsTab(QWidget):
    # 添加API密钥更新信号
    api_key_changed = pyqtSignal(str)
    # 添加设置更新信号
    settings_updated = pyqtSignal()
    
    def __init__(self, config: ConfigManager, api_manager: APIManager, parent=None):
        super().__init__(parent)
        self.config = config
        self.api_manager = api_manager
        self.init_ui()
        self.load_settings()
        
        # 连接API状态变化信号
        self.api_manager.api_status_changed.connect(self.on_api_status_changed)
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # API设置组
        api_group = QGroupBox("API设置")
        api_layout = QFormLayout()
        api_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        api_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        api_layout.setSpacing(10)
        
        # API密钥输入
        api_key_layout = QHBoxLayout()
        api_key_layout.setSpacing(5)
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("请输入API密钥")
        self.test_api_btn = QPushButton("测试API")
        api_key_layout.addWidget(self.api_key_input)
        api_key_layout.addWidget(self.test_api_btn)
        api_layout.addRow("API密钥:", api_key_layout)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # 默认参数设置组
        default_group = QGroupBox("默认参数设置")
        default_layout = QFormLayout()
        default_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        default_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        default_layout.setSpacing(10)

        # 默认模型
        self.default_model_combo = QComboBox()
        self.default_model_combo.addItems([
            "stabilityai/stable-diffusion-3-5-large",
            "stabilityai/stable-diffusion-3-medium", 
            "stabilityai/stable-diffusion-3-5-large-turbo"
        ])
        default_layout.addRow("默认模型:", self.default_model_combo)

        # 默认尺寸
        self.default_size_combo = QComboBox()
        self.default_size_combo.addItems([
            "1024x1024",
            "512x1024",
            "768x512",
            "768x1024",
            "1024x576",
            "576x1024"
        ])
        default_layout.addRow("默认尺寸:", self.default_size_combo)

        # 默认生成数量
        self.default_batch_spin = QSpinBox()
        self.default_batch_spin.setRange(1, 4)
        self.default_batch_spin.setValue(1)
        self.default_batch_spin.setToolTip("单次最多生成4张图片")
        default_layout.addRow("默认生成数量:", self.default_batch_spin)

        # 默认步数
        self.default_steps_spin = QSpinBox()
        self.default_steps_spin.setRange(1, 50)
        self.default_steps_spin.setValue(20)
        self.default_steps_spin.setToolTip("turbo模型固定为4步")
        default_layout.addRow("默认步数:", self.default_steps_spin)

        # 默认引导系数
        self.default_guidance_spin = QDoubleSpinBox()
        self.default_guidance_spin.setRange(0, 20)
        self.default_guidance_spin.setValue(7.5)
        self.default_guidance_spin.setSingleStep(0.5)
        default_layout.addRow("默认引导系数:", self.default_guidance_spin)

        # 默认种子值
        self.default_seed_input = QLineEdit()
        self.default_seed_input.setPlaceholderText("留空表示使用随机种子")
        self.default_seed_input.setToolTip("输入1-9999999999之间的整数作为固定种子值")
        
        # 添加文本变化事件处理
        self.default_seed_input.textChanged.connect(self.validate_seed_input)

        # 添加清空按钮
        clear_seed_btn = QPushButton("清空")
        clear_seed_btn.setFixedWidth(50)
        clear_seed_btn.clicked.connect(lambda: self.default_seed_input.clear())

        # 使用水平布局组合种子输入和清空按钮
        seed_layout = QHBoxLayout()
        seed_layout.addWidget(self.default_seed_input)
        seed_layout.addWidget(clear_seed_btn)
        default_layout.addRow("种子值:", seed_layout)

        default_group.setLayout(default_layout)
        layout.addWidget(default_group)
        
        # 路径设置
        path_group = QGroupBox("路径设置")
        path_layout = QFormLayout()
        path_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        path_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        path_layout.setSpacing(10)
        
        # 输出目录选择
        output_dir_layout = QHBoxLayout()
        output_dir_layout.setSpacing(5)
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("请选择输出目录")
        self.select_dir_btn = QPushButton("浏览...")
        output_dir_layout.addWidget(self.output_dir)
        output_dir_layout.addWidget(self.select_dir_btn)
        path_layout.addRow("输出目录:", output_dir_layout)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # 命名规则设置
        naming_group = QGroupBox("命名规则设置")
        naming_layout = QFormLayout()
        naming_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        naming_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        naming_layout.setSpacing(10)

        # 预设规则选择
        self.naming_rule_combo = QComboBox()
        self.naming_rule_combo.addItems([
            "自定义规则",
            "{timestamp}_{prompt}",  # 时间戳_提示词
            "{date}_{time}_{model}",  # 日期_时间_模型
            "{prompt}_{seed}_{model}",  # 提示词_种子_模型
            "{date}_{prompt}_{index}",  # 日期_提示词_序号
            "{model}_{timestamp}_{seed}"  # 模型_时间戳_种子
        ])
        naming_layout.addRow("预设规则:", self.naming_rule_combo)

        # 自定义规则输入
        self.custom_rule_input = QLineEdit()
        self.custom_rule_input.setPlaceholderText("例如: {date}_{prompt}_{seed}")
        naming_layout.addRow("自定义规则:", self.custom_rule_input)

        # 添加规则说明标签
        rule_info = """
支持的变量:
{timestamp} - 时间戳
{date} - 日期 (YYYYMMDD)
{time} - 时间 (HHMMSS)
{prompt} - 提示词 (前20字符)
{model} - 模型名称
{seed} - 随机种子
{index} - 序号 (多图时)
{size} - 图片尺寸
"""
        info_label = QLabel(rule_info)
        info_label.setStyleSheet("color: gray;")
        naming_layout.addRow("", info_label)

        naming_group.setLayout(naming_layout)
        layout.addWidget(naming_group)
        
        # 保存按钮
        self.save_btn = QPushButton("保存设置")
        self.save_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        # 添加弹性空间
        layout.addStretch()
        
        self.setLayout(layout)
        
        # 连接信号
        self.test_api_btn.clicked.connect(self.test_api_key)
        self.select_dir_btn.clicked.connect(self.select_output_dir)
        self.save_btn.clicked.connect(self.save_settings)
        self.naming_rule_combo.currentTextChanged.connect(self.on_naming_rule_changed)
    
    def on_api_status_changed(self, is_ready: bool):
        """API状态变化处理"""
        self.test_api_btn.setEnabled(not is_ready)
    
    def on_naming_rule_changed(self, rule: str):
        """处理命名规则选择变化"""
        if rule == "自定义规则":
            self.custom_rule_input.setEnabled(True)
        else:
            self.custom_rule_input.setEnabled(False)
            self.custom_rule_input.setText(rule)
    
    def load_settings(self):
        """加载已保存的设置"""
        # 加载API密钥
        api_key = self.config.get("api.key", "")
        self.api_key_input.setText(api_key)
        
        # 加载默认参数设置
        defaults = self.config.get("defaults", {})
        
        # 默认模型
        default_model = defaults.get("model", "stabilityai/stable-diffusion-3-5-large")
        index = self.default_model_combo.findText(default_model)
        if index >= 0:
            self.default_model_combo.setCurrentIndex(index)
            
        # 默认尺寸
        default_size = defaults.get("size", "1024x1024")
        index = self.default_size_combo.findText(default_size)
        if index >= 0:
            self.default_size_combo.setCurrentIndex(index)
            
        # 默认生成数量
        self.default_batch_spin.setValue(defaults.get("batch_size", 1))
        
        # 默认步数
        self.default_steps_spin.setValue(defaults.get("steps", 20))
        
        # 默认引导系数
        self.default_guidance_spin.setValue(defaults.get("guidance", 7.5))
        
        # 默认种子值
        seed = defaults.get("seed")
        if seed is not None:
            self.default_seed_input.setText(str(seed))
        else:
            self.default_seed_input.clear()
        
        # 加载输出目录
        output_dir = self.config.get("paths.output_dir", "")
        self.output_dir.setText(output_dir)
        
        # 加载命名规则设置
        naming_rule = self.config.get("naming.rule", "{timestamp}_{prompt}")
        if naming_rule in [self.naming_rule_combo.itemText(i) for i in range(self.naming_rule_combo.count())]:
            self.naming_rule_combo.setCurrentText(naming_rule)
        else:
            self.naming_rule_combo.setCurrentText("自定义规则")
            self.custom_rule_input.setText(naming_rule)
    
    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir.setText(dir_path)
    
    def test_api_key(self):
        """测试API密钥"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "警告", "请先输入API密钥")
            return
        
        # 禁用测试按钮
        self.test_api_btn.setEnabled(False)
        self.test_api_btn.setText("测试中...")
        
        # 创建并启动测试线程
        self.test_thread = APITestThread(api_key)
        self.test_thread.success.connect(self.on_test_success)
        self.test_thread.error.connect(self.on_test_error)
        self.test_thread.finished.connect(self.on_test_complete)
        self.test_thread.start()
    
    def on_test_success(self):
        """API测试成功处理"""
        # 保存 API 密钥并刷新 API 管理器
        api_key = self.api_key_input.text().strip()
        self.config.set("api.key", api_key)
        self.api_manager.refresh_api()
        QMessageBox.information(self, "成功", "API密钥验证成功")
    
    def on_test_error(self, error_msg: str):
        """API测试失败处理"""
        QMessageBox.critical(self, "错误", error_msg)
    
    def on_test_complete(self):
        """API测试完成处理"""
        # 恢复按钮状态
        self.test_api_btn.setEnabled(True)
        self.test_api_btn.setText("测试API")
    
    def save_settings(self):
        """保存设置"""
        try:
            # 保存API密钥
            api_key = self.api_key_input.text().strip()
            self.config.set("api.key", api_key)
            
            # 保存默认参数设置
            defaults = {
                "model": self.default_model_combo.currentText(),
                "size": self.default_size_combo.currentText(),
                "batch_size": self.default_batch_spin.value(),
                "steps": self.default_steps_spin.value(),
                "guidance": self.default_guidance_spin.value(),
            }
            
            # 只有当种子值不为空时才保存
            seed_text = self.default_seed_input.text().strip()
            if seed_text:
                try:
                    seed_value = int(seed_text)
                    if 1 <= seed_value <= 9999999999:
                        defaults["seed"] = seed_value
                    else:
                        raise ValueError("种子值超出范围")
                except ValueError:
                    QMessageBox.warning(self, "错误", "种子值必须是1-9999999999之间的整数")
                    return
            
            self.config.set("defaults", defaults)
            
            # 保存输出目录
            output_dir = self.output_dir.text().strip()
            if output_dir:
                self.config.set("paths.output_dir", output_dir)
            
            # 保存命名规则
            rule = self.naming_rule_combo.currentText()
            if rule == "自定义规则":
                rule = self.custom_rule_input.text().strip()
            self.config.set("naming.rule", rule)
            
            # 保存配置
            self.config.save_config()
            
            # 刷新API管理器
            self.api_manager.refresh_api()
            
            # 发送设置更新信号
            self.settings_updated.emit()
            
            QMessageBox.information(self, "提示", "设置已保存")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存设置失败: {str(e)}") 
    
    def validate_seed_input(self, text):
        """验证种子值输入"""
        if not text:  # 允许空值
            return
            
        # 只允许输入数字
        if not text.isdigit():
            self.default_seed_input.setText(text.rstrip("非数字字符"))
            return
            
        # 验证数值范围
        try:
            value = int(text)
            if value > 9999999999:
                self.default_seed_input.setText("9999999999")
            elif value < 1 and text != "":
                self.default_seed_input.setText("1")
        except ValueError:
            pass 
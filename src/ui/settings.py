from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                           QPushButton, QGroupBox, QFileDialog, QMessageBox, QHBoxLayout, 
                           QSizePolicy, QComboBox, QLabel, QSpinBox, QDoubleSpinBox, 
                           QCheckBox, QTabWidget)
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
    """设置标签页"""
    settings_updated = pyqtSignal()  # 设置更新信号
    
    def __init__(self, config: ConfigManager, api_manager: APIManager):
        super().__init__()
        self.config = config
        self.api_manager = api_manager
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 基本设置标签页
        basic_tab = QWidget()
        basic_layout = QVBoxLayout()
        basic_tab.setLayout(basic_layout)
        
        # API设置
        api_group = QGroupBox("API设置")
        api_layout = QFormLayout()
        api_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        api_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        api_layout.setSpacing(10)
        
        # API密钥输入
        api_key_layout = QHBoxLayout()
        api_key_layout.setSpacing(5)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("请输入API密钥")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)  # 设置为密码模式
        self.test_api_btn = QPushButton("测试API")
        self.test_api_btn.clicked.connect(self.test_api_key)
        api_key_layout.addWidget(self.api_key_input)
        api_key_layout.addWidget(self.test_api_btn)
        api_layout.addRow("API密钥:", api_key_layout)
        
        api_group.setLayout(api_layout)
        basic_layout.addWidget(api_group)
        
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
        self.select_dir_btn.clicked.connect(self.select_output_dir)
        output_dir_layout.addWidget(self.output_dir)
        output_dir_layout.addWidget(self.select_dir_btn)
        path_layout.addRow("输出目录:", output_dir_layout)
        
        path_group.setLayout(path_layout)
        basic_layout.addWidget(path_group)
        
        # 命名规则设置
        naming_group = QGroupBox("命名规则设置")
        naming_layout = QFormLayout()
        naming_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        naming_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        naming_layout.setSpacing(10)
        
        # 预设规则选择
        self.naming_rule_combo = QComboBox()
        self.naming_rule_combo.addItems([
            "默认",
            "{timestamp}_{prompt}_{model}_{size}_{seed}",
            "{date}_{time}_{prompt}_{model}_{size}",
            "自定义规则"
        ])
        self.naming_rule_combo.currentTextChanged.connect(self.on_naming_rule_changed)
        
        # 自定义规则输入和保存按钮布局
        custom_rule_layout = QHBoxLayout()
        self.custom_rule_input = QLineEdit()
        self.custom_rule_input.setPlaceholderText("请输入自定义命名规则")
        self.custom_rule_input.setEnabled(False)
        
        save_rule_btn = QPushButton("保存为预设")
        save_rule_btn.clicked.connect(self.save_custom_rule)
        custom_rule_layout.addWidget(self.custom_rule_input)
        custom_rule_layout.addWidget(save_rule_btn)
        
        naming_layout.addRow("预设规则:", self.naming_rule_combo)
        naming_layout.addRow("自定义规则:", custom_rule_layout)
        
        # 添加变量说明
        variables_label = QLabel(
            "支持的变量:\n"
            "{timestamp} - 时间戳\n"
            "{date} - 日期 (YYYYMMDD)\n"
            "{time} - 时间 (HHMMSS)\n"
            "{prompt} - 提示词 (前20字符)\n"
            "{model} - 模型名称\n"
            "{seed} - 随机种子\n"
            "{index} - 序号 (多图时)"
        )
        variables_label.setStyleSheet("color: gray;")
        naming_layout.addRow("", variables_label)
        
        naming_group.setLayout(naming_layout)
        basic_layout.addWidget(naming_group)
        basic_layout.addStretch()
        
        # 默认参数设置标签页
        defaults_tab = QWidget()
        defaults_layout = QVBoxLayout()
        defaults_tab.setLayout(defaults_layout)
        
        # 默认参数设置
        defaults_group = QGroupBox("默认参数设置")
        defaults_form = QFormLayout()
        defaults_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        defaults_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        defaults_form.setSpacing(10)
        
        # 默认模型
        self.default_model_combo = QComboBox()
        self.default_model_combo.addItems([
            "stabilityai/stable-diffusion-3-5-large",
            "stabilityai/stable-diffusion-3-medium",
            "stabilityai/stable-diffusion-3-5-large-turbo"
        ])
        defaults_form.addRow("默认模型:", self.default_model_combo)
        
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
        defaults_form.addRow("默认尺寸:", self.default_size_combo)
        
        # 默认生成数量
        self.default_batch_spin = QSpinBox()
        self.default_batch_spin.setRange(1, 4)
        self.default_batch_spin.setValue(1)
        defaults_form.addRow("默认生成数量:", self.default_batch_spin)
        
        # 默认步数
        self.default_steps_spin = QSpinBox()
        self.default_steps_spin.setRange(1, 50)
        self.default_steps_spin.setValue(20)
        defaults_form.addRow("默认步数:", self.default_steps_spin)
        
        # 默认引导系数
        self.default_guidance_spin = QDoubleSpinBox()
        self.default_guidance_spin.setRange(0, 20)
        self.default_guidance_spin.setValue(7.5)
        self.default_guidance_spin.setSingleStep(0.5)
        defaults_form.addRow("默认引导系数:", self.default_guidance_spin)
        
        # 默认负面提示词
        self.default_negative_prompt = QLineEdit()
        self.default_negative_prompt.setPlaceholderText("请输入默认负面提示词（可选）")
        defaults_form.addRow("默认负面提示词:", self.default_negative_prompt)
        
        # 默认种子值
        self.default_seed_input = QLineEdit()
        self.default_seed_input.setPlaceholderText("留空表示使用随机种子")
        self.default_seed_input.setToolTip("输入1-9999999998之间的整数作为固定种子值")
        self.default_seed_input.textChanged.connect(self.validate_seed_input)
        defaults_form.addRow("默认种子值:", self.default_seed_input)
        
        # 默认使用随机种子
        self.default_random_seed_check = QCheckBox("默认使用随机种子")
        self.default_random_seed_check.stateChanged.connect(self.on_random_seed_changed)
        defaults_form.addRow("", self.default_random_seed_check)
        
        defaults_group.setLayout(defaults_form)
        defaults_layout.addWidget(defaults_group)
        defaults_layout.addStretch()
        
        # 添加标签页
        tab_widget.addTab(basic_tab, "基本设置")
        tab_widget.addTab(defaults_tab, "默认参数")
        
        layout.addWidget(tab_widget)
        
        # 保存按钮
        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_btn)
    
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
        """加载设置"""
        try:
            # 加载API密钥
            api_key = self.config.get("api_key", "")
            self.api_key_input.setText(api_key)
            
            # 加载默认参数
            defaults = self.config.get("defaults", {})
            
            # 更新尺寸
            default_size = defaults.get("size", "1024x1024")
            index = self.default_size_combo.findText(default_size)
            if index >= 0:
                self.default_size_combo.setCurrentIndex(index)
            
            # 更新其他参数
            self.default_steps_spin.setValue(defaults.get("steps", 20))
            self.default_guidance_spin.setValue(defaults.get("guidance", 7.5))
            self.default_negative_prompt.setText(defaults.get("negative_prompt", ""))
            
            # 更新种子值设置
            use_random = defaults.get("use_random_seed", False)
            self.default_random_seed_check.setChecked(use_random)
            
            if use_random:
                self.default_seed_input.clear()
            else:
                seed = defaults.get("seed")
                if seed is not None:
                    self.default_seed_input.setText(str(seed))
                else:
                    self.default_seed_input.clear()
            
            # 加载路径设置
            paths = self.config.get("paths", {})
            self.output_dir.setText(paths.get("output_dir", ""))
            
            # 加载命名规则
            naming_rule = self.config.get("naming.rule", "{timestamp}_{prompt}_{model}_{size}_{seed}")
            # 检查是否是预设规则
            index = self.naming_rule_combo.findText(naming_rule)
            if index >= 0:
                self.naming_rule_combo.setCurrentIndex(index)
            else:
                # 如果不是预设规则，设置为自定义规则
                self.naming_rule_combo.setCurrentText("自定义规则")
                self.custom_rule_input.setText(naming_rule)
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载设置失败: {str(e)}")
    
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
            
            # 保存默认参数
            defaults = {
                "model": self.default_model_combo.currentText(),
                "size": self.default_size_combo.currentText(),
                "batch_size": self.default_batch_spin.value(),
                "steps": self.default_steps_spin.value(),
                "guidance": self.default_guidance_spin.value(),
                "negative_prompt": self.default_negative_prompt.text().strip(),
                "use_random_seed": self.default_random_seed_check.isChecked()
            }
            
            # 只有在不使用随机种子且有输入值时才保存种子值
            if not self.default_random_seed_check.isChecked() and self.default_seed_input.text().strip():
                try:
                    seed_value = int(self.default_seed_input.text().strip())
                    if 1 <= seed_value <= 9999999998:  # 修改为正确的范围
                        defaults["seed"] = seed_value
                except ValueError:
                    pass
            
            self.config.set("defaults", defaults)
            
            # 保存输出目录
            output_dir = self.output_dir.text().strip()
            if output_dir:
                self.config.set("paths.output_dir", output_dir)
            
            # 保存命名规则
            rule = self.naming_rule_combo.currentText()
            if rule == "自定义规则":
                rule = self.custom_rule_input.text().strip()
                if not rule:
                    QMessageBox.warning(self, "错误", "自定义命名规则不能为空")
                    return
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
    
    def on_random_seed_changed(self, state):
        """处理随机种子复选框状态变化"""
        is_checked = state == Qt.CheckState.Checked.value
        self.default_seed_input.setEnabled(not is_checked)
        if is_checked:
            self.default_seed_input.clear()
    
    def validate_seed_input(self, text):
        """验证种子值输入"""
        if not text:  # 允许空值
            return
            
        # 只允许输入数字
        if not text.isdigit():
            self.default_seed_input.clear()  # 清除非数字输入
            return
            
        # 验证数值范围 (0 < x < 9999999999)
        try:
            value = int(text)
            if value >= 9999999999:
                self.default_seed_input.setText("9999999998")
            elif value < 1 and text != "":
                self.default_seed_input.setText("1")
        except ValueError:
            self.default_seed_input.clear()  # 清除无效输入
    
    def save_custom_rule(self):
        """保存自定义规则到预设"""
        custom_rule = self.custom_rule_input.text().strip()
        if not custom_rule:
            QMessageBox.warning(self, "错误", "请先输入自定义命名规则")
            return
            
        # 检查是否已存在
        if self.naming_rule_combo.findText(custom_rule) >= 0:
            QMessageBox.warning(self, "错误", "该规则已存在于预设中")
            return
            
        # 添加到预设列表
        self.naming_rule_combo.insertItem(self.naming_rule_combo.count() - 1, custom_rule)
        
        # 选择新添加的规则
        self.naming_rule_combo.setCurrentText(custom_rule)
        QMessageBox.information(self, "成功", "自定义规则已添加到预设") 
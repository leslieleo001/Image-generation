"""单图生成标签页模块"""

import os
import random
import requests
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QCheckBox, QListWidget, QListWidgetItem,
    QMessageBox, QApplication, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon

from ..utils.config_manager import ConfigManager
from ..utils.api_manager import APIManager
from ..utils.history_manager import HistoryManager
from .history_window import HistoryWindow

class ImageGenerationThread(QThread):
    """图片生成线程"""
    progress = pyqtSignal(str)  # 进度信号
    error = pyqtSignal(str)     # 错误信号
    success = pyqtSignal(list)  # 成功信号，传递保存的文件列表
    
    def __init__(self, api, params, save_dir, naming_rule):
        super().__init__()
        self.api = api
        self.params = params
        self.save_dir = save_dir
        self.naming_rule = naming_rule
        
    def run(self):
        try:
            saved_files = []
            batch_size = self.params["batch_size"]
            seeds = self.params.get("seeds", [])
            
            # 显示详细的生成进度
            self.progress.emit("=== 开始生成 ===")
            self.progress.emit(f"• 准备生成 {batch_size} 张图片")
            self.progress.emit(f"• 使用模型: {self.params['model']}")
            self.progress.emit(f"• 图片尺寸: {self.params['image_size']}")
            self.progress.emit(f"• 生成步数: {self.params['num_inference_steps']}")
            self.progress.emit(f"• 引导系数: {self.params['guidance_scale']}")
            self.progress.emit(f"• 使用的种子值: {', '.join(map(str, seeds))}")
            self.progress.emit("=== 调用API ===")
            
            # 调用API生成图片
            try:
                result = self.api.generate_image(
                    prompt=self.params["prompt"].strip(),
                    model=self.params["model"],
                    negative_prompt=self.params["negative_prompt"].strip(),
                    size=self.params["image_size"],
                    batch_size=batch_size,
                    num_inference_steps=self.params["num_inference_steps"],
                    guidance_scale=self.params["guidance_scale"],
                    prompt_enhancement=self.params["enhance_prompt"],
                    seeds=seeds  # 使用seeds而不是seed
                )
                
                # 显示推理时间
                if isinstance(result, dict) and "timings" in result:
                    inference_time = result["timings"].get("inference", 0)
                    self.progress.emit(f"• 推理完成，耗时: {inference_time:.2f}秒")
                
            except Exception as e:
                error_msg = str(e)
                if "IPM limit reached" in error_msg:
                    self.error.emit("API请求超出限额，请联系服务商增加额度")
                elif "Invalid API key" in error_msg:
                    self.error.emit("API密钥无效，请检查设置")
                elif "Request processing has failed" in error_msg:
                    self.error.emit("服务器处理请求失败，请稍后重试")
                elif "Connection" in error_msg:
                    self.error.emit("网络连接失败，请检查网络设置")
                elif "Timeout" in error_msg:
                    self.error.emit("请求超时，请检查网络状态或稍后重试")
                else:
                    self.error.emit(f"API请求失败: {error_msg}")
                return
            
            if not result:
                self.error.emit("生成失败: API返回为空")
                return
            
            # 检查返回的数据结构
            if isinstance(result, dict):
                if "error" in result:
                    self.error.emit(f"API返回错误: {result['error']}")
                    return
                elif "data" in result:
                    images = result["data"]
                elif "images" in result:
                    images = result["images"]
                else:
                    self.error.emit("API返回数据格式错误")
                    return
            else:
                self.error.emit("API返回数据类型错误")
                return
            
            if not images:
                self.error.emit("未获取到图片数据")
                return
            
            # 验证返回的图片数量
            if len(images) != batch_size:
                self.error.emit(f"API返回的图片数量({len(images)})与请求数量({batch_size})不符")
                return
            
            # 处理生成的图片
            for i, img_info in enumerate(images):
                try:
                    img_url = img_info.get("url")
                    if not img_url:
                        self.error.emit(f"第{i+1}张图片URL为空")
                        continue
                    
                    self.progress.emit(f"• 正在下载第 {i+1}/{batch_size} 张图片")
                    self.progress.emit(f"  - 种子值: {seeds[i]}")
                    self.progress.emit(f"  - 提示词: {self.params['prompt'][:50]}...")
                    
                    # 下载图片
                    response = requests.get(img_url, timeout=30)
                    if response.status_code != 200:
                        self.error.emit(f"图片下载失败, 状态码: {response.status_code}")
                        continue
                    
                    # 生成唯一的文件名
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')  # 添加毫秒以确保唯一性
                    date = datetime.now().strftime('%Y%m%d')
                    time = datetime.now().strftime('%H%M%S')
                    
                    # 替换命名规则中的变量
                    file_name = self.naming_rule
                    file_name = file_name.replace("{timestamp}", timestamp)
                    file_name = file_name.replace("{date}", date)
                    file_name = file_name.replace("{time}", time)
                    file_name = file_name.replace("{prompt}", self.params["prompt"][:30].replace(" ", "_"))  # 限制提示词长度
                    file_name = file_name.replace("{model}", self.params["model"].split("/")[-1])
                    file_name = file_name.replace("{size}", self.params["image_size"])
                    file_name = file_name.replace("{seed}", str(seeds[i]))
                    file_name = file_name.replace("{index}", f"{i+1:02d}")  # 添加前导零的序号
                    file_name = file_name.replace("{batch_index}", f"{i+1:02d}of{batch_size:02d}")  # 批次信息
                    
                    # 如果命名规则中没有包含序号相关的变量，强制添加序号
                    if "{index}" not in self.naming_rule and "{batch_index}" not in self.naming_rule:
                        file_name = f"{i+1:02d}_{file_name}"
                    
                    # 清理文件名中的非法字符
                    file_name = "".join(c for c in file_name if c.isalnum() or c in "._- ")
                    # 确保文件名不会太长
                    if len(file_name) > 200:
                        file_name = file_name[:200]
                    file_name = f"{file_name}.png"
                    
                    # 确保文件名唯一
                    file_path = os.path.join(self.save_dir, file_name)
                    base_name, ext = os.path.splitext(file_name)
                    counter = 1
                    while os.path.exists(file_path):
                        new_name = f"{base_name}_{counter}{ext}"
                        file_path = os.path.join(self.save_dir, new_name)
                        counter += 1
                    
                    self.progress.emit(f"• 正在保存第 {i+1}/{batch_size} 张图片")
                    self.progress.emit(f"  - 保存路径: {file_path}")
                    
                    # 保存图片
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    saved_files.append((file_path, seeds[i]))  # 保存文件路径和种子值
                    
                except Exception as e:
                    self.error.emit(f"处理图片时出错: {str(e)}")
                    continue
            
            if not saved_files:
                self.error.emit("生成失败: 所有图片保存失败")
            else:
                self.success.emit(saved_files)
                
        except Exception as e:
            self.error.emit(str(e))

class SingleGenTab(QWidget):
    """单图生成标签页"""
    
    def __init__(self, config: ConfigManager, api_manager: APIManager):
        super().__init__()
        self.config = config
        self.api_manager = api_manager
        
        # 初始化历史记录管理器
        self.history_manager = HistoryManager()
        # 连接历史记录更新信号
        self.history_manager.history_updated.connect(self.load_history)
        
        # 历史记录窗口
        self.history_window = None
        
        # 初始化界面
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout()
        
        # 左侧面板 - 参数设置
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # 提示词输入
        prompt_label = QLabel("提示词:")
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("请输入提示词...")
        self.prompt_input.setMaximumHeight(100)
        
        # 负面提示词输入
        negative_label = QLabel("负面提示词:")
        self.negative_input = QTextEdit()
        self.negative_input.setPlaceholderText("请输入负面提示词...")
        self.negative_input.setMaximumHeight(100)
        
        # 获取默认值
        defaults = self.config.get("defaults", {})
        
        # 模型选择
        model_label = QLabel("模型:")
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "stabilityai/stable-diffusion-3-5-large",
            "stabilityai/stable-diffusion-3-medium", 
            "stabilityai/stable-diffusion-3-5-large-turbo"
        ])
        # 设置默认模型
        default_model = defaults.get("model", "stabilityai/stable-diffusion-3-5-large")
        index = self.model_combo.findText(default_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        
        # 图片尺寸选择
        size_label = QLabel("尺寸:")
        self.size_combo = QComboBox()
        self.size_combo.addItems([
            "1024x1024",
            "512x1024",
            "768x512",
            "768x1024",
            "1024x576",
            "576x1024"
        ])
        # 设置默认尺寸
        default_size = defaults.get("size", "1024x1024")
        index = self.size_combo.findText(default_size)
        if index >= 0:
            self.size_combo.setCurrentIndex(index)
        
        # 生成数量
        batch_label = QLabel("生成数量:")
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 4)
        self.batch_spin.setValue(1)  # 设置默认值为1
        self.batch_spin.setToolTip("单次最多生成4张图片")
        
        # 生成步数
        steps_label = QLabel("步数:")
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(1, 50)
        self.steps_spin.setValue(defaults.get("steps", 20))
        self.steps_spin.setToolTip("turbo模型固定为4步")
        
        # 引导系数
        guidance_label = QLabel("引导系数:")
        self.guidance_spin = QDoubleSpinBox()
        self.guidance_spin.setRange(0, 20)
        self.guidance_spin.setValue(defaults.get("guidance", 7.5))
        self.guidance_spin.setSingleStep(0.5)
        
        # 种子值设置
        seed_layout = QHBoxLayout()
        self.random_seed_check = QCheckBox("使用随机种子")
        self.random_seed_check.stateChanged.connect(self.on_random_seed_changed)
        
        self.seed_input = QLineEdit()
        self.seed_input.setPlaceholderText("留空表示使用随机种子")
        self.seed_input.setToolTip("输入1-9999999999之间的整数作为固定种子值")
        self.seed_input.textChanged.connect(self.validate_seed_input)
        
        # 清空按钮
        clear_seed_btn = QPushButton("清空")
        clear_seed_btn.setFixedWidth(50)
        clear_seed_btn.clicked.connect(lambda: self.seed_input.clear())
        
        seed_layout.addWidget(self.seed_input)
        seed_layout.addWidget(clear_seed_btn)
        
        seed_group = QVBoxLayout()
        seed_group.addWidget(self.random_seed_check)
        seed_group.addLayout(seed_layout)
        
        # 提示增强
        self.enhance_check = QCheckBox("提示增强")
        self.enhance_check.setToolTip("启用后将优化提示词以提高生成质量")
        
        # 生成按钮和进度标签
        gen_progress_layout = QVBoxLayout()
        self.generate_btn = QPushButton("生成图片")
        self.generate_btn.clicked.connect(self.on_generate_clicked)
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gen_progress_layout.addWidget(self.generate_btn)
        gen_progress_layout.addWidget(self.progress_label)
        
        # 添加控件到左侧面板
        left_layout.addWidget(prompt_label)
        left_layout.addWidget(self.prompt_input)
        left_layout.addWidget(negative_label)
        left_layout.addWidget(self.negative_input)
        left_layout.addWidget(model_label)
        left_layout.addWidget(self.model_combo)
        left_layout.addWidget(size_label)
        left_layout.addWidget(self.size_combo)
        left_layout.addWidget(batch_label)
        left_layout.addWidget(self.batch_spin)
        left_layout.addWidget(steps_label)
        left_layout.addWidget(self.steps_spin)
        left_layout.addWidget(guidance_label)
        left_layout.addWidget(self.guidance_spin)
        left_layout.addLayout(seed_group)
        left_layout.addWidget(self.enhance_check)
        left_layout.addLayout(gen_progress_layout)
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # 右侧面板 - 历史记录
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # 历史记录标题和管理按钮
        history_header = QHBoxLayout()
        history_label = QLabel("历史记录")
        manage_history_btn = QPushButton("管理")
        manage_history_btn.clicked.connect(self.show_history_window)
        history_header.addWidget(history_label)
        history_header.addWidget(manage_history_btn)
        history_header.addStretch()
        
        # 历史记录列表
        self.history_list = QListWidget()
        self.history_list.setIconSize(QSize(80, 80))
        self.history_list.setSpacing(5)
        self.history_list.itemDoubleClicked.connect(self.on_history_item_double_clicked)
        
        # 清空历史按钮
        clear_history_btn = QPushButton("清空历史")
        clear_history_btn.clicked.connect(self.on_clear_history_clicked)
        
        right_layout.addLayout(history_header)
        right_layout.addWidget(self.history_list)
        right_layout.addWidget(clear_history_btn)
        right_panel.setLayout(right_layout)
        
        # 设置布局
        layout.addWidget(left_panel, stretch=2)
        layout.addWidget(right_panel, stretch=1)
        self.setLayout(layout)
        
        # 加载历史记录
        self.load_history()
        
        # 连接模型选择变更事件
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        
    def load_history(self):
        """加载历史记录"""
        records = self.history_manager.get_records()
        self.history_list.clear()
        for record in records:
            item = QListWidgetItem()
            
            # 获取所有图片路径
            image_paths = record.get("image_paths", [])
            if not image_paths and "image_path" in record:  # 兼容旧格式
                image_paths = [record["image_path"]]
            
            # 创建缩略图
            if image_paths:
                # 使用第一张图片作为主缩略图
                if os.path.exists(image_paths[0]):
                    pixmap = QPixmap(image_paths[0])
                    scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio)
                    item.setIcon(QIcon(scaled_pixmap))
            
            # 设置文本（使用文件名而不是时间戳）
            filename = "未知"
            if image_paths:
                filename = os.path.splitext(os.path.basename(image_paths[0]))[0]
                if len(image_paths) > 1:
                    filename += f" (+{len(image_paths)-1})"
            
            params = record.get("params", {})
            prompt = params.get("prompt", "")[:50]
            image_count = len(image_paths)
            item.setText(f"{filename}\n{prompt}\n[{image_count}张图片]")
            
            # 设置数据
            item.setData(Qt.ItemDataRole.UserRole, record)
            self.history_list.addItem(item)
            
    def show_history_window(self):
        """显示历史记录管理窗口"""
        if not self.history_window:
            self.history_window = HistoryWindow(self.history_manager)
        self.history_window.show()
        self.history_window.activateWindow()
        
    def on_history_item_double_clicked(self, item):
        """处理历史记录双击事件"""
        record = item.data(Qt.ItemDataRole.UserRole)
        if not record:
            return
        
        params = record.get("params", {})
        
        # 恢复参数
        self.prompt_input.setPlainText(params.get("prompt", ""))
        self.negative_input.setPlainText(params.get("negative_prompt", ""))
        
        # 设置模型
        model = params.get("model", "")
        index = self.model_combo.findText(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        
        # 设置尺寸
        size = params.get("size", "")
        index = self.size_combo.findText(size)
        if index >= 0:
            self.size_combo.setCurrentIndex(index)
        
        # 设置其他参数
        self.steps_spin.setValue(params.get("num_inference_steps", 20))
        self.guidance_spin.setValue(params.get("guidance_scale", 7.5))
        
        # 处理seed值
        seeds = params.get("seeds", [])
        if seeds:
            self.seed_input.setText(str(seeds[0]))  # 使用第一个种子值
        else:
            self.seed_input.clear()
        
        self.enhance_check.setChecked(params.get("prompt_enhancement", False))
        
        # 打开所有图片
        image_paths = record.get("image_paths", [])
        if not image_paths and "image_path" in record:  # 兼容旧格式
            image_paths = [record["image_path"]]
        
        for path in image_paths:
            if os.path.exists(path):
                os.startfile(path)

    def on_clear_history_clicked(self):
        """处理清空历史按钮点击事件"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清空所有历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.clear_records()
            self.load_history()

    def on_model_changed(self, model_name):
        """处理模型选择变更"""
        if "turbo" in model_name.lower():
            self.steps_spin.setValue(4)
            self.steps_spin.setEnabled(False)
        else:
            self.steps_spin.setEnabled(True)

    def on_generate_clicked(self):
        """处理生成按钮点击"""
        try:
            # 获取参数
            prompt = self.prompt_input.toPlainText().strip()
            if not prompt:
                QMessageBox.warning(self, "错误", "请输入提示词")
                return
                
            negative = self.negative_input.toPlainText().strip()
            model = self.model_combo.currentText()
            size = self.size_combo.currentText()
            steps = self.steps_spin.value()
            guidance = self.guidance_spin.value()
            enhance = self.enhance_check.isChecked()
            batch_size = self.batch_spin.value()
            
            # 处理种子值
            if not self.random_seed_check.isChecked() and self.seed_input.text().strip():
                try:
                    seed_value = int(self.seed_input.text().strip())
                    if 1 <= seed_value <= 9999999999:
                        seeds = [seed_value] * batch_size  # 使用相同的种子值
                    else:
                        raise ValueError("种子值超出范围")
                except ValueError:
                    QMessageBox.warning(self, "错误", "种子值必须是1-9999999999之间的整数")
                    return
            else:
                # 为每张图片生成不同的随机种子 (0 < x < 9999999999)
                seeds = [random.randint(1, 9999999998) for _ in range(batch_size)]
            
            # 构建参数字典
            self.params = {
                "prompt": prompt,
                "negative_prompt": negative,
                "model": model,
                "image_size": size,
                "num_inference_steps": steps,
                "guidance_scale": guidance,
                "seeds": seeds,  # 使用seeds而不是seed
                "enhance_prompt": enhance,
                "batch_size": batch_size
            }
            
            # 获取保存路径
            save_dir = self.config.get("paths.output_dir")
            if not save_dir:
                save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "图片保存")
            os.makedirs(save_dir, exist_ok=True)
            
            # 获取命名规则
            naming_rule = self.config.get("naming.rule", "{timestamp}_{prompt}_{model}_{size}_{seed}")
            print(f"使用命名规则: {naming_rule}")  # 添加日志
            
            # 禁用生成按钮
            self.generate_btn.setEnabled(False)
            self.generate_btn.setText("生成中...")
            self.progress_label.setText("准备生成...")
            
            # 创建并启动生成线程
            self.gen_thread = ImageGenerationThread(
                self.api_manager.api,
                self.params,  # 使用保存的参数
                save_dir,
                naming_rule
            )
            
            # 连接信号
            self.gen_thread.progress.connect(self.update_progress)
            self.gen_thread.error.connect(self.on_generation_error)
            self.gen_thread.success.connect(self.on_generation_success)
            self.gen_thread.finished.connect(self.on_generation_finished)
            
            # 启动线程
            self.gen_thread.start()
            
        except Exception as e:
            self.on_generation_error(str(e))
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("生成图片")
    
    def update_progress(self, message):
        """更新进度提示"""
        self.progress_label.setText(message)
        QApplication.processEvents()
    
    def on_generation_error(self, error_msg):
        """处理生成错误"""
        QMessageBox.warning(self, "错误", error_msg)
        print(f"生成图片时出错: {error_msg}")
    
    def on_generation_success(self, saved_files):
        """处理生成成功"""
        # 为每张图片添加一条历史记录
        for file_path, seed in saved_files:
            history_item = {
                "timestamp": datetime.now().isoformat(),
                "params": {
                    "prompt": self.prompt_input.toPlainText().strip(),
                    "negative_prompt": self.negative_input.toPlainText().strip(),
                    "model": self.model_combo.currentText(),
                    "size": self.size_combo.currentText(),
                    "num_inference_steps": self.steps_spin.value(),
                    "guidance_scale": self.guidance_spin.value(),
                    "seed": seed,  # 使用实际使用的种子值
                    "prompt_enhancement": self.enhance_check.isChecked(),
                    "batch_size": 1  # 每条记录都是单张图片
                },
                "image_paths": [file_path]  # 单张图片路径
            }
            self.history_manager.add_record(history_item)
        
        self.load_history()
        QMessageBox.information(self, "提示", f"生成完成，已保存{len(saved_files)}张图片")
    
    def on_generation_finished(self):
        """生成完成后的清理工作"""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("生成图片")
        self.progress_label.setText("")
        self.gen_thread = None

    def randomize_seed(self):
        """生成新的随机种子"""
        self.seed_input.setText(str(random.randint(1, 9999999998)))  # 1 到 9999999998

    def update_defaults(self):
        """更新默认参数设置"""
        defaults = self.config.get("defaults", {})
        
        # 更新模型
        default_model = defaults.get("model", "stabilityai/stable-diffusion-3-5-large")
        index = self.model_combo.findText(default_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        
        # 更新尺寸
        default_size = defaults.get("size", "1024x1024")
        index = self.size_combo.findText(default_size)
        if index >= 0:
            self.size_combo.setCurrentIndex(index)
        
        # 更新其他参数
        self.batch_spin.setValue(defaults.get("batch_size", 1))
        self.steps_spin.setValue(defaults.get("steps", 20))
        self.guidance_spin.setValue(defaults.get("guidance", 7.5))
        
        # 更新负面提示词
        negative_prompt = defaults.get("negative_prompt", "")
        self.negative_input.setPlainText(negative_prompt)
        
        # 更新种子值设置
        use_random = defaults.get("use_random_seed", False)
        self.random_seed_check.setChecked(use_random)
        
        if use_random:
            self.seed_input.clear()
        else:
            seed = defaults.get("seed")
            if seed is not None:
                self.seed_input.setText(str(seed))
            else:
                self.seed_input.clear()

    def on_random_seed_changed(self, state):
        """处理随机种子复选框状态变化"""
        is_checked = state == Qt.CheckState.Checked.value
        self.seed_input.setEnabled(not is_checked)
        if is_checked:
            self.seed_input.clear()

    def validate_seed_input(self, text):
        """验证种子值输入"""
        if not text:  # 允许空值
            return
            
        # 只允许输入数字
        if not text.isdigit():
            self.seed_input.setText(text.rstrip("非数字字符"))
            return
            
        # 验证数值范围 (0 < x < 9999999999)
        try:
            value = int(text)
            if value >= 9999999999:
                self.seed_input.setText("9999999998")
            elif value < 1 and text != "":
                self.seed_input.setText("1")
        except ValueError:
            pass

    def get_generation_params(self):
        """获取生成参数"""
        params = {
            "prompt": self.prompt_input.toPlainText().strip(),
            "negative_prompt": self.negative_input.toPlainText().strip(),
            "model": self.model_combo.currentText(),
            "size": self.size_combo.currentText(),
            "num_inference_steps": self.steps_spin.value(),
            "guidance_scale": self.guidance_spin.value(),
            "prompt_enhancement": self.enhance_check.isChecked(),
            "batch_size": self.batch_spin.value()
        }
        
        # 处理种子值
        if not self.random_seed_check.isChecked() and self.seed_input.text().strip():
            try:
                seed_value = int(self.seed_input.text().strip())
                if 1 <= seed_value <= 9999999998:  # 修改为正确的范围
                    params["seed"] = seed_value
                else:
                    raise ValueError("种子值超出范围")
            except ValueError:
                QMessageBox.warning(self, "错误", "种子值必须是1-9999999998之间的整数")
                return None
        else:
            # 使用随机种子时，为每张图片生成不同的随机种子
            if params["batch_size"] > 1:
                params["seed"] = [random.randint(1, 9999999998) for _ in range(params["batch_size"])]  # 1 到 9999999998
            else:
                params["seed"] = random.randint(1, 9999999998)  # 1 到 9999999998
        
        return params

# ... existing code ... 
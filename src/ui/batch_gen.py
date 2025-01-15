import os
import random
import requests
from datetime import datetime
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QGroupBox, QListWidget, QListWidgetItem, QTextEdit,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon

from src.utils.api_client import SiliconFlowAPI
from src.utils.api_manager import APIManager
from src.utils.config_manager import ConfigManager
from src.utils.history_manager import HistoryManager

class BatchGenerationThread(QThread):
    """批量生成线程"""
    progress = pyqtSignal(str)  # 进度信号
    error = pyqtSignal(str)     # 错误信号
    finished = pyqtSignal(list)  # 完成信号，传递生成的文件列表
    image_saved = pyqtSignal(dict)  # 单张图片保存完成信号
    
    def __init__(self, api, prompts, params, save_dir, naming_rule):
        super().__init__()
        self.api = api
        self.prompts = prompts
        self.params = params
        self.save_dir = save_dir
        self.naming_rule = naming_rule
        self.is_running = True
        self.saved_files = []  # 保存已生成的文件路径
    
    def save_image(self, img_url, seeds, j, prompt, params):
        """保存单张图片并发送记录"""
        try:
            response = requests.get(img_url, timeout=30)
            if response.status_code != 200:
                return None
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            date = datetime.now().strftime('%Y%m%d')
            time = datetime.now().strftime('%H%M%S')
            
            # 处理命名规则
            filename = str(self.naming_rule)
            replacements = {
                "{timestamp}": timestamp,
                "{date}": date,
                "{time}": time,
                "{prompt}": prompt[:30].replace(" ", "_"),  # 限制提示词长度
                "{model}": self.params["model"].split("/")[-1],
                "{size}": self.params["size"],
                "{seed}": str(seeds[j]),
                "{index}": f"{j+1:02d}"
            }
            
            # 应用替换
            for key, value in replacements.items():
                filename = filename.replace(key, value)
            
            # 确保文件名合法
            filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
            # 限制文件名长度
            if len(filename) > 100:  # 减小最大长度以适应完整路径
                filename = filename[:100]
            filename = f"{filename}.png"
            
            # 确保保存目录存在
            os.makedirs(self.save_dir, exist_ok=True)
            
            # 保存图片
            filepath = os.path.join(self.save_dir, filename)
            
            # 确保文件名唯一
            base_name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(filepath):
                new_name = f"{base_name}_{counter}{ext}"
                filepath = os.path.join(self.save_dir, new_name)
                counter += 1
            
            # 检查最终路径长度
            if len(filepath) > 250:  # Windows MAX_PATH 限制
                short_name = f"{j+1:02d}_{timestamp[:8]}_{seeds[j]}.png"
                filepath = os.path.join(self.save_dir, short_name)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            # 创建该图片的记录
            record = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "params": {
                    "prompt": prompt,
                    "negative_prompt": params["negative_prompt"],
                    "model": params["model"],
                    "size": params["size"],
                    "num_inference_steps": params["steps"],
                    "guidance_scale": params["guidance"],
                    "seed": seeds[j],
                    "source": "batch"
                },
                "image_path": filepath
            }
            
            self.image_saved.emit(record)
            return filepath
            
        except Exception as e:
            if self.is_running:
                self.error.emit(f"保存图片时出错: {str(e)}")
            return None
    
    def run(self):
        try:
            total = len(self.prompts)
            
            for i, prompt in enumerate(self.prompts, 1):
                if not self.is_running:
                    self.progress.emit("生成已取消")
                    self.finished.emit(self.saved_files)
                    return
                
                # 生成随机种子列表
                if self.params["seed"] == -1:
                    seeds = [random.randint(1, 9999999998) for _ in range(self.params["batch_size"])]
                else:
                    seeds = [self.params["seed"]] * self.params["batch_size"]
                
                self.progress.emit(f"=== 处理第 {i}/{total} 个提示词 ===")
                self.progress.emit(f"• 提示词: {prompt}")
                self.progress.emit(f"• 使用模型: {self.params['model']}")
                self.progress.emit(f"• 图片尺寸: {self.params['size']}")
                self.progress.emit(f"• 生成步数: {self.params['steps']}")
                self.progress.emit(f"• 引导系数: {self.params['guidance']}")
                self.progress.emit(f"• 使用的种子值: {', '.join(map(str, seeds))}")
                self.progress.emit("=== 调用API ===")
                
                try:
                    # 调用API生成图片
                    result = self.api.generate_image(
                        prompt=prompt,
                        model=self.params["model"],
                        negative_prompt=self.params["negative_prompt"],
                        size=self.params["size"],
                        batch_size=self.params["batch_size"],
                        num_inference_steps=self.params["steps"],
                        guidance_scale=self.params["guidance"],
                        prompt_enhancement=False,
                        seeds=seeds
                    )
                    
                    if not self.is_running:
                        self.progress.emit("生成已取消")
                        self.finished.emit(self.saved_files)
                        return
                    
                    # 处理生成的图片
                    images = result.get("data", [])
                    for j, img_info in enumerate(images):
                        if not self.is_running:
                            self.progress.emit("生成已取消")
                            self.finished.emit(self.saved_files)
                            return
                        
                        img_url = img_info.get("url")
                        if not img_url:
                            continue
                            
                        # 保存图片并获取文件路径
                        filepath = self.save_image(img_url, seeds, j, prompt, self.params)
                        if filepath:
                            self.saved_files.append(filepath)
                            self.progress.emit(f"• 已保存第 {j+1}/{len(images)} 张图片")
                            self.progress.emit(f"  - 种子值: {seeds[j]}")
                            self.progress.emit(f"  - 提示词: {prompt[:50]}...")
                            self.progress.emit(f"  - 保存路径: {filepath}")
                
                except Exception as e:
                    if self.is_running:
                        self.error.emit(f"生成第{i}个提示词时出错: {str(e)}")
                    continue
            
            if self.is_running:
                self.progress.emit("生成完成")
            else:
                self.progress.emit("生成已取消")
            
            self.finished.emit(self.saved_files)
            
        except Exception as e:
            if self.is_running:
                self.error.emit(f"批量生成过程出错: {str(e)}")
            self.finished.emit(self.saved_files)
    
    def stop(self):
        """停止生成"""
        self.is_running = False

class BatchGenTab(QWidget):
    """批量生成标签页"""
    
    def __init__(self, api_manager, config_manager, history_manager):
        super().__init__()
        self.api_manager = api_manager
        self.config_manager = config_manager
        self.history_manager = history_manager
        self.tasks = []
        self.current_task_index = 0
        self.is_cancelling = False
        
        # 创建按钮
        self.start_btn = QPushButton("开始生成")
        self.pause_btn = QPushButton("暂停")
        self.resume_btn = QPushButton("继续")
        self.cancel_btn = QPushButton("取消")
        self.clear_btn = QPushButton("清空任务")
        self.import_btn = QPushButton("导入Excel参数")
        self.template_btn = QPushButton("下载参数模板")
        
        # 设置按钮初始状态
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        
        # 连接按钮点击事件
        self.start_btn.clicked.connect(self.on_generate_clicked)
        self.pause_btn.clicked.connect(self.pause_generation)
        self.resume_btn.clicked.connect(self.resume_generation)
        self.cancel_btn.clicked.connect(self.cancel_generation)
        self.clear_btn.clicked.connect(self.clear_tasks)
        self.import_btn.clicked.connect(self.import_excel)
        self.template_btn.clicked.connect(self.download_template)
        
        # 初始化界面
        self.init_ui()
    
    def update_progress_text(self, text):
        """更新进度文本"""
        self.progress_text.append(text)
        # 滚动到底部
        scrollbar = self.progress_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_generation_error(self, error_msg):
        """处理生成错误"""
        QMessageBox.warning(self, "错误", error_msg)
        # 恢复界面状态
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.clear_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
    
    def on_generation_finished(self, saved_files):
        """生成完成的处理"""
        # 恢复界面状态
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.clear_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        
        if self.is_cancelling:
            self.update_progress_text(f"已取消生成，保存了{len(saved_files)}张图片")
            self.is_cancelling = False
        else:
            self.update_progress_text("生成完成！")
            if saved_files:
                QMessageBox.information(self, "完成", f"批量生成完成，已保存{len(saved_files)}张图片！")

    def init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout()
        
        # 左侧面板 - 基本控制
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Excel操作按钮
        excel_group = QGroupBox("Excel操作")
        excel_layout = QVBoxLayout()
        excel_layout.addWidget(self.import_btn)
        excel_layout.addWidget(self.template_btn)
        excel_group.setLayout(excel_layout)
        
        # 生成控制按钮
        control_group = QGroupBox("生成控制")
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.resume_btn)
        control_layout.addWidget(self.cancel_btn)
        control_layout.addWidget(self.clear_btn)
        control_group.setLayout(control_layout)
        
        # 添加到左侧布局
        left_layout.addWidget(excel_group)
        left_layout.addWidget(control_group)
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # 右侧面板 - 任务列表和进度
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # 任务列表
        task_group = QGroupBox("任务列表")
        task_layout = QVBoxLayout()
        self.task_list = QListWidget()
        task_layout.addWidget(self.task_list)
        task_group.setLayout(task_layout)
        
        # 进度显示
        progress_group = QGroupBox("生成进度")
        progress_layout = QVBoxLayout()
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        progress_layout.addWidget(self.progress_text)
        progress_group.setLayout(progress_layout)
        
        right_layout.addWidget(task_group, 2)  # 任务列表占2份
        right_layout.addWidget(progress_group, 1)  # 进度显示占1份
        right_panel.setLayout(right_layout)
        
        # 设置左右面板的比例
        layout.addWidget(left_panel, 1)  # 左侧面板占1份
        layout.addWidget(right_panel, 3)  # 右侧面板占3份
        
        self.setLayout(layout)

    def download_template(self):
        """下载Excel参数模板"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存模板",
            "batch_generation_template.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if filename:
            try:
                # 获取默认参数
                defaults = self.config_manager.get("defaults", {})
                
                # 创建示例数据
                data = {
                    "prompt": ["1girl, beautiful", "1boy, handsome"],
                    "negative_prompt": [defaults.get("negative_prompt", "")] * 2,
                    "model": [defaults.get("model", "stabilityai/stable-diffusion-3-5-large")] * 2,
                    "size": [defaults.get("size", "1024x1024")] * 2,
                    "steps": [defaults.get("steps", 20)] * 2,
                    "guidance": [defaults.get("guidance", 7.5)] * 2,
                    "batch_size": [defaults.get("batch_size", 1)] * 2,
                    "seed": ["", ""],  # 留空表示使用随机种子
                    "enhance_prompt": [defaults.get("enhance_prompt", False)] * 2
                }
                
                df = pd.DataFrame(data)
                df.to_excel(filename, index=False)
                
                QMessageBox.information(self, "成功", "模板已下载，你可以按照模板格式填写参数。\n注意：种子值留空表示使用随机种子，或填入1-9999999998之间的整数作为固定种子值。")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"下载模板失败: {str(e)}")

    def import_excel(self):
        """从Excel导入参数"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls)"
            )
            if not file_path:
                return
            
            df = pd.read_excel(file_path)
            if df.empty:
                QMessageBox.warning(self, "警告", "Excel文件为空")
                return
            
            # 清空任务列表
            self.task_list.clear()
            self.tasks = []
            
            # 导入任务
            for _, row in df.iterrows():
                try:
                    prompt = row.get("prompt", "").strip()
                    if not prompt:  # 跳过空提示词
                        continue
                    
                    # 创建任务项
                    task_info = {
                        "prompt": prompt,
                        "negative_prompt": str(row.get("negative_prompt", "")),
                        "model": str(row.get("model", "stabilityai/stable-diffusion-3-5-large")),
                        "size": str(row.get("size", "1024x1024")),
                        "steps": int(row.get("steps", 20)),
                        "guidance": float(row.get("guidance", 7.5)),
                        "batch_size": int(row.get("batch_size", 1)),
                        "seed": int(row.get("seed", -1)) if pd.notna(row.get("seed")) else -1,
                        "enhance_prompt": bool(row.get("enhance_prompt", False))
                    }
                    
                    # 添加到任务列表
                    item = QListWidgetItem(f"提示词: {prompt[:50]}...")
                    item.setData(Qt.ItemDataRole.UserRole, task_info)
                    self.task_list.addItem(item)
                    self.tasks.append(task_info)
                    
                except Exception as e:
                    print(f"导入任务时出错: {str(e)}")
                    continue
            
            # 更新界面状态
            self.start_btn.setEnabled(bool(self.tasks))
            self.clear_btn.setEnabled(bool(self.tasks))
            
            if self.tasks:
                QMessageBox.information(self, "成功", f"成功导入 {len(self.tasks)} 个任务")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导入失败: {str(e)}")

    def pause_generation(self):
        """暂停生成"""
        if hasattr(self, 'gen_thread') and self.gen_thread and self.gen_thread.isRunning():
            self.gen_thread.stop()
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.update_progress_text("已暂停生成")

    def resume_generation(self):
        """恢复生成"""
        if hasattr(self, 'gen_thread') and self.gen_thread:
            self.gen_thread.is_running = True
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.update_progress_text("继续生成")

    def on_generate_clicked(self):
        """处理生成按钮点击事件"""
        try:
            if not self.tasks:
                QMessageBox.warning(self, "提示", "请先导入任务")
                return
            
            # 获取保存目录
            save_dir = self.config_manager.get("paths", {}).get("output_dir", "")
            if not save_dir:
                QMessageBox.warning(self, "提示", "请先在设置中配置输出目录")
                return
            
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            # 获取命名规则
            naming_rule = self.config_manager.get("naming_rule", "{timestamp}_{prompt}_{model}_{size}_{seed}")
            
            # 创建并启动生成线程
            self.gen_thread = BatchGenerationThread(
                self.api_manager.api,
                [task["prompt"] for task in self.tasks],
                self.tasks[0],  # 使用第一个任务的参数作为基础参数
                save_dir,
                naming_rule
            )
            
            # 连接信号
            self.gen_thread.progress.connect(self.update_progress_text)
            self.gen_thread.error.connect(self.on_generation_error)
            self.gen_thread.finished.connect(self.on_generation_finished)
            self.gen_thread.image_saved.connect(self.on_image_saved)  # 连接新的信号
            
            # 更新界面状态
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.clear_btn.setEnabled(False)
            self.import_btn.setEnabled(False)
            
            # 重置取消状态
            self.is_cancelling = False
            
            # 启动线程
            self.gen_thread.start()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"启动生成失败: {str(e)}")
            self.start_btn.setEnabled(True)

    def clear_tasks(self):
        """清空任务"""
        self.task_list.clear()  # 清空任务列表
        self.tasks = []  # 清空任务数组
        self.progress_text.clear()  # 清空进度文本
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.import_btn.setEnabled(True)  # 启用导入按钮

    def update_defaults(self):
        """更新默认参数设置"""
        # 批量生成界面不需要实时更新默认参数
        # 因为所有参数都是从Excel导入的
        pass

    def cancel_generation(self):
        """取消生成"""
        if hasattr(self, 'gen_thread') and self.gen_thread and self.gen_thread.isRunning():
            if self.is_cancelling:  # 避免重复取消
                return
                
            reply = QMessageBox.question(
                self,
                "确认取消",
                "确定要取消当前任务吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.is_cancelling = True
                self.update_progress_text("正在取消生成...")
                
                # 停止生成线程
                self.gen_thread.stop()
                
                # 禁用所有按钮，防止重复操作
                self.start_btn.setEnabled(False)
                self.pause_btn.setEnabled(False)
                self.resume_btn.setEnabled(False)
                self.cancel_btn.setEnabled(False)
                self.clear_btn.setEnabled(False)
                self.import_btn.setEnabled(False)

    def on_image_saved(self, record):
        """处理单张图片保存完成事件"""
        # 直接添加到历史记录
        self.history_manager.add_record({
            "timestamp": record["timestamp"],
            "params": record["params"],
            "image_paths": [record["image_path"]]  # 转换为列表格式
        })
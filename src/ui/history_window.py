import os
from datetime import datetime
from pathlib import Path
import pandas as pd
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QPushButton, 
    QLabel, QFileDialog, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon
from src.utils.history_manager import HistoryManager

class HistoryWindow(QMainWindow):
    def __init__(self, history_manager):
        super().__init__()
        self.history_manager = history_manager
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("历史记录管理")
        self.resize(1200, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建工具栏
        toolbar = QHBoxLayout()
        export_btn = QPushButton("导出Excel")
        export_btn.clicked.connect(self.export_to_excel)
        delete_btn = QPushButton("删除选中")
        delete_btn.clicked.connect(self.delete_selected)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_table)
        
        toolbar.addWidget(export_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "缩略图", "时间", "提示词", "模型", "参数", "保存路径", "操作"
        ])
        
        # 设置表格列宽
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 100)  # 缩略图列宽
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 100)  # 操作列宽
        
        layout.addWidget(self.table)
        
        # 加载数据
        self.refresh_table()
        
    def refresh_table(self):
        """刷新表格数据"""
        self.table.setRowCount(0)
        records = self.history_manager.get_records()
        
        for record in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 缩略图
            image_paths = record.get("image_paths", [])  # 获取所有图片路径
            if not image_paths and "image_path" in record:  # 兼容旧格式
                image_paths = [record["image_path"]]
            
            if image_paths:
                # 创建缩略图容器
                thumb_widget = QWidget()
                thumb_layout = QHBoxLayout(thumb_widget)
                thumb_layout.setContentsMargins(2, 2, 2, 2)
                thumb_layout.setSpacing(2)
                
                # 显示最多4张缩略图
                for path in image_paths[:4]:
                    if os.path.exists(path):
                        pixmap = QPixmap(path)
                        scaled_pixmap = pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio)
                        label = QLabel()
                        label.setPixmap(scaled_pixmap)
                        thumb_layout.addWidget(label)
                
                if len(image_paths) > 4:
                    more_label = QLabel(f"+{len(image_paths)-4}")
                    thumb_layout.addWidget(more_label)
                
                thumb_layout.addStretch()
                self.table.setCellWidget(row, 0, thumb_widget)
            
            # 时间
            timestamp = record.get("timestamp", "")
            self.table.setItem(row, 1, QTableWidgetItem(timestamp))
            
            # 提示词
            params = record.get("params", {})
            prompt = params.get("prompt", "")
            self.table.setItem(row, 2, QTableWidgetItem(prompt))
            
            # 模型
            model = params.get("model", "")
            self.table.setItem(row, 3, QTableWidgetItem(model))
            
            # 参数
            param_text = f"尺寸: {params.get('size', '')}\n"
            param_text += f"步数: {params.get('num_inference_steps', '')}\n"
            param_text += f"引导系数: {params.get('guidance_scale', '')}\n"
            param_text += f"数量: {len(image_paths)}"
            self.table.setItem(row, 4, QTableWidgetItem(param_text))
            
            # 保存路径
            path_text = "\n".join(image_paths)
            self.table.setItem(row, 5, QTableWidgetItem(path_text))
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            
            # 添加打开文件夹按钮
            folder_btn = QPushButton("打开文件夹")
            folder_btn.clicked.connect(lambda checked, paths=image_paths: self.open_folder(paths[0]))
            btn_layout.addWidget(folder_btn)
            
            # 添加打开图片按钮
            if len(image_paths) == 1:
                open_btn = QPushButton("打开")
                open_btn.clicked.connect(lambda checked, path=image_paths[0]: self.open_image(path))
                btn_layout.addWidget(open_btn)
            
            self.table.setCellWidget(row, 6, btn_widget)
    
    def open_image(self, path):
        """打开图片"""
        if os.path.exists(path):
            os.startfile(path)
        else:
            QMessageBox.warning(self, "错误", "图片文件不存在")
    
    def delete_selected(self):
        """删除选中的记录"""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            return
            
        reply = QMessageBox.question(
            self,
            "确认",
            f"确定要删除选中的 {len(selected_rows)} 条记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 从后往前删除，避免索引变化
            for row in sorted(selected_rows, reverse=True):
                # 删除图片文件
                image_path = self.table.item(row, 5).text()
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except Exception as e:
                        print(f"删除图片文件失败: {str(e)}")
                
                # 从历史记录中删除
                self.history_manager.records.pop(row)
            
            # 保存更改
            self.history_manager.save_records()
            # 刷新表格
            self.refresh_table()
    
    def export_to_excel(self):
        """导出为Excel"""
        try:
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出Excel",
                "",
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return
                
            # 准备数据
            data = []
            records = self.history_manager.get_records()
            
            for record in records:
                params = record.get("params", {})
                row = {
                    "时间": record.get("timestamp", ""),
                    "提示词": params.get("prompt", ""),
                    "负面提示词": params.get("negative_prompt", ""),
                    "模型": params.get("model", ""),
                    "尺寸": params.get("size", ""),
                    "步数": params.get("num_inference_steps", ""),
                    "引导系数": params.get("guidance_scale", ""),
                    "随机种子": params.get("seed", ""),
                    "提示增强": params.get("prompt_enhancement", False),
                    "图片路径": record.get("image_path", "")
                }
                data.append(row)
            
            # 创建DataFrame并保存
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, engine="openpyxl")
            
            QMessageBox.information(self, "提示", "导出成功")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导出失败: {str(e)}") 
    
    def open_folder(self, path):
        """打开文件夹"""
        if os.path.exists(path):
            folder_path = os.path.dirname(path)
            os.startfile(folder_path)
        else:
            QMessageBox.warning(self, "错误", "文件夹不存在") 
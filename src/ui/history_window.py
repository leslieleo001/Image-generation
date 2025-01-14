import os
from datetime import datetime
from pathlib import Path
import pandas as pd
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QPushButton, 
    QLabel, QFileDialog, QMessageBox, QHeaderView, QMenu,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QSize, QPointF
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor
from src.utils.history_manager import HistoryManager

class DraggableTableWidget(QTableWidget):
    """支持拖放的表格控件"""
    def __init__(self, history_window):
        super().__init__(history_window)
        self.history_manager = None
        self.history_window = history_window
        self.drag_source_row = -1
        self.drop_indicator_row = -1
        
        # 启用拖放
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
        self.setDragDropOverwriteMode(False)
        self.setShowGrid(True)
        self.setAlternatingRowColors(True)
        
        # 设置样式
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #e5f3ff;
            }
        """)
        
    def startDrag(self, supportedActions):
        """开始拖动时记录源行"""
        self.drag_source_row = self.currentRow()
        super().startDrag(supportedActions)
        
    def dropEvent(self, event):
        """处理拖放事件"""
        if not self.history_manager or self.drag_source_row < 0:
            event.ignore()
            return
            
        # 获取目标行
        drop_row = self.drop_indicator_row
        if drop_row < 0:
            drop_row = self.rowCount() - 1
            
        # 如果是相同位置，不处理
        if self.drag_source_row == drop_row:
            event.ignore()
            return
            
        try:
            # 记住当前的滚动位置
            scrollbar = self.verticalScrollBar()
            scroll_pos = scrollbar.value()
            
            # 暂时阻止信号
            self.blockSignals(True)
            
            # 移动记录
            record = self.history_manager.records.pop(self.drag_source_row)
            if drop_row > self.drag_source_row:
                drop_row -= 1
            self.history_manager.records.insert(drop_row, record)
            
            # 保存更改并发送更新信号
            self.history_manager.save_records()
            
            # 直接根据history_manager.records重新填充表格内容
            for row, record in enumerate(self.history_manager.records):
                # 复选框
                checkbox_item = QTableWidgetItem()
                checkbox_item.setCheckState(Qt.CheckState.Unchecked)
                self.setItem(row, 0, checkbox_item)
                
                # 缩略图
                image_paths = record.get("image_paths", [])
                if not image_paths and "image_path" in record:
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
                    self.setCellWidget(row, 1, thumb_widget)
                
                # 名称
                if image_paths:
                    filename = os.path.splitext(os.path.basename(image_paths[0]))[0]
                    if len(image_paths) > 1:
                        filename += f" (+{len(image_paths)-1})"
                    self.setItem(row, 2, QTableWidgetItem(filename))
                else:
                    self.setItem(row, 2, QTableWidgetItem("未知"))
                
                # 提示词
                params = record.get("params", {})
                prompt = params.get("prompt", "")
                self.setItem(row, 3, QTableWidgetItem(prompt))
                
                # 模型
                model = params.get("model", "")
                self.setItem(row, 4, QTableWidgetItem(model))
                
                # 参数
                param_text = f"尺寸: {params.get('size', '')}\n"
                param_text += f"步数: {params.get('num_inference_steps', '')}\n"
                param_text += f"引导系数: {params.get('guidance_scale', '')}\n"
                param_text += f"数量: {len(image_paths)}"
                self.setItem(row, 5, QTableWidgetItem(param_text))
                
                # 保存路径
                path_text = "\n".join(image_paths)
                self.setItem(row, 6, QTableWidgetItem(path_text))
                
                # 操作列（空）
                empty_widget = QWidget()
                self.setCellWidget(row, 7, empty_widget)
            
            # 恢复信号
            self.blockSignals(False)
            
            # 恢复滚动位置
            scrollbar.setValue(scroll_pos)
            
            # 选中移动后的行
            self.selectRow(drop_row)
            
            # 发送历史记录更新信号
            self.history_manager.history_updated.emit()
            
        except Exception as e:
            print(f"拖放处理出错: {str(e)}")
            event.ignore()
        finally:
            self.drag_source_row = -1
            self.drop_indicator_row = -1
            self.viewport().update()
            
    def dragEnterEvent(self, event):
        """处理拖动进入事件"""
        if event.source() == self:
            event.accept()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        """处理拖动移动事件"""
        if event.source() == self:
            # 计算目标行
            pos = event.position().toPoint()
            row = self.rowAt(pos.y())
            
            # 处理拖到表格末尾的情况
            if row < 0:
                row = self.rowCount()
            
            # 更新拖放指示器位置
            self.drop_indicator_row = row
            self.viewport().update()
            event.accept()
        else:
            event.ignore()
            
    def paintEvent(self, event):
        """绘制事件，用于显示拖放指示器"""
        super().paintEvent(event)
        
        # 如果正在拖动，绘制指示器
        if self.drag_source_row >= 0 and self.drop_indicator_row >= 0:
            painter = QPainter(self.viewport())
            painter.setPen(QPen(QColor("#0078d7"), 2, Qt.PenStyle.SolidLine))
            
            # 计算指示器位置
            if self.drop_indicator_row < self.rowCount():
                rect = self.visualRect(self.model().index(self.drop_indicator_row, 0))
                y = rect.top()
            else:
                rect = self.visualRect(self.model().index(self.rowCount()-1, 0))
                y = rect.bottom()
                
            # 绘制水平线
            width = self.viewport().width()
            painter.drawLine(0, y, width, y)
            
            # 绘制小三角形指示器
            triangle_size = 6
            painter.setBrush(QBrush(QColor("#0078d7")))
            
            # 左侧三角形
            points = [
                QPointF(-triangle_size, y),
                QPointF(0, y - triangle_size),
                QPointF(0, y + triangle_size)
            ]
            painter.drawPolygon(points)
            
            # 右侧三角形
            points = [
                QPointF(width + triangle_size, y),
                QPointF(width, y - triangle_size),
                QPointF(width, y + triangle_size)
            ]
            painter.drawPolygon(points)

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
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all_records)
        unselect_all_btn = QPushButton("取消全选")
        unselect_all_btn.clicked.connect(self.unselect_all_records)
        export_btn = QPushButton("导出选中Excel")
        export_btn.clicked.connect(self.export_to_excel)
        delete_btn = QPushButton("删除选中")
        delete_btn.clicked.connect(self.delete_selected)
        delete_with_files_btn = QPushButton("删除选中(含图片)")
        delete_with_files_btn.clicked.connect(lambda: self.delete_selected(True))
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_table)
        
        toolbar.addWidget(select_all_btn)
        toolbar.addWidget(unselect_all_btn)
        toolbar.addWidget(export_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addWidget(delete_with_files_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # 创建表格
        self.table = DraggableTableWidget(self)
        self.table.history_manager = self.history_manager
        self.table.setColumnCount(8)  # 增加一列用于复选框
        self.table.setHorizontalHeaderLabels([
            "选择", "缩略图", "名称", "提示词", "模型", "参数", "保存路径", "操作"
        ])
        
        # 设置表格列宽
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)  # 复选框列宽
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 100)  # 缩略图列宽
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 100)  # 操作列宽
        
        # 添加右键菜单
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)
        
        # 加载数据
        self.refresh_table()
        
    def select_all_records(self):
        """全选所有记录"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
                
    def unselect_all_records(self):
        """取消全选"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
    
    def get_checked_rows(self):
        """获取所有选中的行"""
        checked_rows = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                checked_rows.append(row)
        return checked_rows
    
    def refresh_table(self):
        """刷新表格数据"""
        records = self.history_manager.get_records()
        
        # 先设置正确的行数
        self.table.setRowCount(len(records))
        
        # 更新表格内容
        for idx, record in enumerate(records):
            # 添加复选框
            checkbox_item = QTableWidgetItem()
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(idx, 0, checkbox_item)
            
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
                self.table.setCellWidget(idx, 1, thumb_widget)
            
            # 名称（使用文件名，不带扩展名）
            if image_paths:
                filename = os.path.splitext(os.path.basename(image_paths[0]))[0]
                if len(image_paths) > 1:
                    filename += f" (+{len(image_paths)-1})"
                self.table.setItem(idx, 2, QTableWidgetItem(filename))
            else:
                self.table.setItem(idx, 2, QTableWidgetItem("未知"))
            
            # 提示词
            params = record.get("params", {})
            prompt = params.get("prompt", "")
            self.table.setItem(idx, 3, QTableWidgetItem(prompt))
            
            # 模型
            model = params.get("model", "")
            self.table.setItem(idx, 4, QTableWidgetItem(model))
            
            # 参数
            param_text = f"尺寸: {params.get('size', '')}\n"
            param_text += f"步数: {params.get('num_inference_steps', '')}\n"
            param_text += f"引导系数: {params.get('guidance_scale', '')}\n"
            param_text += f"数量: {len(image_paths)}"
            self.table.setItem(idx, 5, QTableWidgetItem(param_text))
            
            # 保存路径
            path_text = "\n".join(image_paths)
            self.table.setItem(idx, 6, QTableWidgetItem(path_text))
            
            # 移除操作按钮，改用右键菜单
            empty_widget = QWidget()
            self.table.setCellWidget(idx, 7, empty_widget)
    
    def delete_selected(self, delete_files=False):
        """删除选中的记录
        Args:
            delete_files (bool): 是否同时删除图片文件
        """
        selected_rows = self.get_checked_rows()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的记录")
            return
            
        msg = f"确定要删除选中的 {len(selected_rows)} 条记录"
        if delete_files:
            msg += "及其对应的图片文件"
        msg += "吗？"
        
        reply = QMessageBox.question(
            self,
            "确认",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 从后往前删除，避免索引变化
            for row in sorted(selected_rows, reverse=True):
                # 获取所有图片路径
                path_item = self.table.item(row, 6)  # 路径列的索引变为6
                if path_item:
                    image_paths = path_item.text().split("\n")
                    
                    # 删除图片文件
                    if delete_files:
                        for image_path in image_paths:
                            if os.path.exists(image_path):
                                try:
                                    os.remove(image_path)
                                except Exception as e:
                                    print(f"删除图片文件失败: {str(e)}")
                
                # 从历史记录中删除
                self.history_manager.records.pop(row)
            
            # 保存更改
            self.history_manager.save_records()
            # 发送历史记录更新信号
            self.history_manager.history_updated.emit()
            # 刷新表格
            self.refresh_table()
            
            QMessageBox.information(
                self,
                "提示",
                f"已删除 {len(selected_rows)} 条记录" + ("及其图片文件" if delete_files else "")
            )
    
    def export_to_excel(self):
        """导出选中记录为Excel（包含原图）"""
        try:
            # 获取选中的行
            selected_rows = self.get_checked_rows()
            if not selected_rows:
                QMessageBox.warning(self, "提示", "请先选择要导出的记录")
                return
            
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
            records = self.history_manager.get_records()
            selected_records = [records[row] for row in selected_rows]
            
            # 创建一个新的Excel工作簿
            from openpyxl import Workbook
            from openpyxl.drawing.image import Image
            from openpyxl.utils import get_column_letter
            
            wb = Workbook()
            ws = wb.active
            
            # 设置列标题
            headers = [
                "图片", "名称", "提示词", "负面提示词", "模型", 
                "尺寸", "步数", "引导系数", "随机种子", "提示增强", 
                "图片路径"
            ]
            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)
            
            # 设置第一列的宽度（用于显示图片）
            ws.column_dimensions['A'].width = 40  # 增加列宽以显示更大的图片
            
            # 设置行高
            ws.row_dimensions[1].height = 15  # 标题行高度
            
            # 填充数据
            for row_idx, record in enumerate(selected_records, 2):  # 从第2行开始（第1行是标题）
                params = record.get("params", {})
                image_paths = record.get("image_paths", [])
                if not image_paths and "image_path" in record:  # 兼容旧格式
                    image_paths = [record["image_path"]]
                
                # 处理图片
                if image_paths:
                    try:
                        # 获取第一张图片
                        img_path = image_paths[0]
                        if os.path.exists(img_path):
                            # 直接使用原图
                            img = Image(img_path)
                            
                            # 设置合适的显示大小（保持原始比例）
                            max_height = 300  # 最大显示高度
                            scale = min(1.0, max_height / img.height)
                            img.width = img.width * scale
                            img.height = img.height * scale
                            
                            # 设置行高以适应图片
                            ws.row_dimensions[row_idx].height = img.height * 0.75  # 转换为Excel单位
                            
                            # 将图片添加到单元格
                            ws.add_image(img, f'A{row_idx}')
                    except Exception as e:
                        print(f"处理图片失败: {str(e)}")
                
                # 获取文件名（不带扩展名）
                filename = "未知"
                if image_paths:
                    filename = os.path.splitext(os.path.basename(image_paths[0]))[0]
                    if len(image_paths) > 1:
                        filename += f" (+{len(image_paths)-1})"
                
                # 填充其他列
                row_data = [
                    "",  # 第一列是图片
                    filename,  # 名称列
                    params.get("prompt", ""),
                    params.get("negative_prompt", ""),
                    params.get("model", ""),
                    params.get("size", ""),
                    params.get("num_inference_steps", ""),
                    params.get("guidance_scale", ""),
                    params.get("seed", ""),
                    "是" if params.get("prompt_enhancement", False) else "否",
                    "\n".join(image_paths)
                ]
                
                for col, value in enumerate(row_data, 1):
                    cell = ws.cell(row=row_idx, column=col, value=value)
                    # 对于长文本，启用自动换行
                    if isinstance(value, str) and len(value) > 50:
                        cell.alignment = cell.alignment.copy(wrapText=True)
            
            # 调整列宽
            for col in range(2, len(headers) + 1):
                ws.column_dimensions[get_column_letter(col)].width = 20
            
            # 保存Excel文件
            wb.save(file_path)
            
            QMessageBox.information(self, "提示", f"已导出 {len(selected_records)} 条记录")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导出失败: {str(e)}")
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        # 获取点击的行
        item = self.table.itemAt(pos)
        if not item:
            return
            
        row = item.row()
        path_item = self.table.item(row, 6)  # 路径列的索引变为6
        if not path_item:
            return
            
        # 获取图片路径
        image_paths = path_item.text().split("\n")
        if not image_paths:
            return
            
        # 创建右键菜单
        menu = QMenu(self)
        open_image = menu.addAction("打开图片")
        open_folder = menu.addAction("打开图片位置")
        
        # 显示菜单并获取选择的动作
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        
        if action == open_image:
            self.open_image(image_paths[0])
        elif action == open_folder:
            self.open_folder(image_paths[0])
            
    def open_image(self, path):
        """打开图片"""
        if os.path.exists(path):
            os.startfile(path)
        else:
            QMessageBox.warning(self, "错误", "图片文件不存在")
    
    def open_folder(self, path):
        """打开文件夹"""
        if os.path.exists(path):
            folder_path = os.path.dirname(path)
            os.startfile(folder_path)
        else:
            QMessageBox.warning(self, "错误", "文件夹不存在") 
from PyQt6.QtWidgets import QLabel, QRubberBand, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, QPointF
from PyQt6.QtGui import QPixmap, QPainter, QWheelEvent, QMouseEvent, QPaintEvent, QResizeEvent

class ImagePreviewWidget(QWidget):
    """图片预览组件，支持缩放、拖动等功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 100)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 创建图片显示标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #cccccc;")
        layout.addWidget(self.image_label)
        
        # 创建导航按钮和计数标签
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("上一张")
        self.prev_btn.clicked.connect(self.previous_image)
        
        self.count_label = QLabel("0/0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.next_btn = QPushButton("下一张")
        self.next_btn.clicked.connect(self.next_image)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.count_label)
        nav_layout.addWidget(self.next_btn)
        layout.addLayout(nav_layout)
        
        self.setLayout(layout)
        
        # 图片相关
        self._pixmaps = []  # 存储多张图片
        self._current_index = 0  # 当前显示的图片索引
        self._scaled_pixmap = None
        self._scale = 1.0
        self._min_scale = 0.1
        self._max_scale = 5.0
        
        # 拖动相关
        self._dragging = False
        self._drag_start = QPoint()
        self._scroll_offset = QPoint()
        
        # 设置组件属性
        self.image_label.setMouseTracking(True)
        self.image_label.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        
    def load_images(self, image_paths: list) -> None:
        """加载多张图片"""
        self._pixmaps = []
        for path in image_paths:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self._pixmaps.append(pixmap)
        
        self._current_index = 0
        self._scale = 1.0
        self._scroll_offset = QPoint()
        
        # 更新导航按钮状态
        self._update_navigation()
        
        if self._pixmaps:
            self._update_scaled_pixmap()
            self.fit_to_view()  # 自动适应窗口大小
            self.update()
    
    def _update_navigation(self) -> None:
        """更新导航按钮和计数显示"""
        total = len(self._pixmaps)
        current = self._current_index + 1 if total > 0 else 0
        
        # 更新计数显示
        self.count_label.setText(f"{current}/{total}")
        
        # 更新按钮状态
        self.prev_btn.setEnabled(total > 1)
        self.next_btn.setEnabled(total > 1)
    
    def next_image(self) -> None:
        """显示下一张图片"""
        if self._pixmaps and len(self._pixmaps) > 1:
            self._current_index = (self._current_index + 1) % len(self._pixmaps)
            self._update_scaled_pixmap()
            self._update_navigation()
            self.update()
    
    def previous_image(self) -> None:
        """显示上一张图片"""
        if self._pixmaps and len(self._pixmaps) > 1:
            self._current_index = (self._current_index - 1) % len(self._pixmaps)
            self._update_scaled_pixmap()
            self._update_navigation()
            self.update()
    
    def keyPressEvent(self, event) -> None:
        """处理键盘事件"""
        if event.key() == Qt.Key.Key_Left:
            self.previous_image()
        elif event.key() == Qt.Key.Key_Right:
            self.next_image()
        else:
            super().keyPressEvent(event)
    
    def _update_scaled_pixmap(self) -> None:
        """更新缩放后的图片"""
        if not self._pixmaps or self._current_index >= len(self._pixmaps):
            self._scaled_pixmap = None
            return
            
        current_pixmap = self._pixmaps[self._current_index]
        # 计算缩放后的尺寸
        scaled_size = current_pixmap.size() * self._scale
        
        # 创建缩放后的图片
        self._scaled_pixmap = current_pixmap.scaled(
            scaled_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # 更新标签显示
        self.image_label.setPixmap(self._scaled_pixmap)
        
    def paintEvent(self, event: QPaintEvent) -> None:
        """重写绘制事件"""
        super().paintEvent(event)
        
    def wheelEvent(self, event: QWheelEvent) -> None:
        """处理鼠标滚轮事件"""
        if not self._pixmaps or self._current_index >= len(self._pixmaps):
            return
            
        # 计算新的缩放比例
        delta = event.angleDelta().y()
        scale_delta = 0.1 if delta > 0 else -0.1
        new_scale = max(self._min_scale, min(self._max_scale, self._scale + scale_delta))
        
        if new_scale != self._scale:
            # 保存鼠标位置相对于图片中心的偏移
            old_pos = QPoint(int(event.position().x()), int(event.position().y()))
            old_center = QPoint(self.image_label.width() // 2, self.image_label.height() // 2)
            old_offset = old_pos - old_center - self._scroll_offset
            
            # 更新缩放
            self._scale = new_scale
            self._update_scaled_pixmap()
            
            # 计算新的偏移以保持鼠标位置不变
            new_offset = QPoint(
                int(old_offset.x() * (new_scale / (new_scale - scale_delta))),
                int(old_offset.y() * (new_scale / (new_scale - scale_delta)))
            )
            self._scroll_offset = old_pos - old_center - new_offset
            
            self.update()
            
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """处理鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_start = event.pos()
            self.image_label.setCursor(Qt.CursorShape.ClosedHandCursor)
            
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """处理鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.image_label.setCursor(Qt.CursorShape.ArrowCursor)
            
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """处理鼠标移动事件"""
        if self._dragging and self._scaled_pixmap:
            # 计算拖动偏移
            delta = event.pos() - self._drag_start
            new_offset = self._scroll_offset + delta
            
            # 计算最大可拖动范围
            max_x = max(0, (self._scaled_pixmap.width() - self.image_label.width()) // 2)
            max_y = max(0, (self._scaled_pixmap.height() - self.image_label.height()) // 2)
            
            # 应用限制
            new_offset.setX(max(-max_x, min(max_x, new_offset.x())))
            new_offset.setY(max(-max_y, min(max_y, new_offset.y())))
            
            # 更新状态
            if new_offset != self._scroll_offset:  # 只在偏移量发生变化时更新
                self._scroll_offset = new_offset
                self._drag_start = event.pos()
                self.update()  # 触发重绘
            
    def resizeEvent(self, event: QResizeEvent) -> None:
        """处理窗口大小改变事件"""
        super().resizeEvent(event)
        if self._pixmaps and self._current_index < len(self._pixmaps):
            self._update_scaled_pixmap()
            
    def reset_view(self) -> None:
        """重置视图"""
        if self._pixmaps and self._current_index < len(self._pixmaps):
            self._scale = 1.0
            self._scroll_offset = QPoint()
            self._update_scaled_pixmap()
            self.update()
            
    def fit_to_view(self) -> None:
        """适应窗口大小"""
        if not self._pixmaps or self._current_index >= len(self._pixmaps):
            return
            
        # 计算适应窗口的缩放比例
        view_size = self.image_label.size()
        pixmap_size = self._pixmaps[self._current_index].size()
        
        # 考虑边距
        margin = 20
        available_width = view_size.width() - 2 * margin
        available_height = view_size.height() - 2 * margin
        
        # 计算缩放比例，保持宽高比
        scale_x = available_width / pixmap_size.width()
        scale_y = available_height / pixmap_size.height()
        
        # 使用较小的缩放比例以确保完整显示
        self._scale = min(scale_x, scale_y)
        self._scroll_offset = QPoint()
        self._update_scaled_pixmap()
        self.update() 
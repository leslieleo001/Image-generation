import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QImage, QWheelEvent
from PyQt6.QtCore import Qt, QPoint, QSize, QPointF
from src.ui.image_preview import ImagePreviewWidget
from PyQt6.QtTest import QTest

@pytest.fixture
def preview_widget(qtbot):
    """创建预览组件"""
    widget = ImagePreviewWidget()
    qtbot.addWidget(widget)
    return widget

@pytest.fixture
def sample_image():
    """创建测试图片"""
    image = QImage(100, 100, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.white)
    return QPixmap.fromImage(image)

def test_init(preview_widget):
    """测试初始化"""
    assert preview_widget.minimumSize() == QSize(100, 100)
    assert preview_widget._scale == 1.0
    assert preview_widget._min_scale == 0.1
    assert preview_widget._max_scale == 5.0
    assert not preview_widget._dragging
    assert preview_widget._scroll_offset == QPoint(0, 0)

def test_set_pixmap(preview_widget, sample_image):
    """测试设置图片"""
    preview_widget.setPixmap(sample_image)
    assert preview_widget._pixmap == sample_image
    assert preview_widget._scale == 1.0
    assert preview_widget._scroll_offset == QPoint(0, 0)
    assert preview_widget._scaled_pixmap is not None

def test_wheel_zoom(qtbot, preview_widget, sample_image):
    """测试滚轮缩放"""
    preview_widget.setPixmap(sample_image)
    initial_scale = preview_widget._scale
    
    # 模拟滚轮事件
    pos = QPointF(100, 100)
    global_pos = QPointF(preview_widget.mapToGlobal(QPoint(100, 100)))
    event = QWheelEvent(
        pos,  # pos
        global_pos,  # globalPos
        QPoint(0, 120),  # pixelDelta
        QPoint(0, 120),  # angleDelta
        Qt.MouseButton.NoButton,  # buttons
        Qt.KeyboardModifier.NoModifier,  # modifiers
        Qt.ScrollPhase.NoScrollPhase,  # phase
        False,  # inverted
        Qt.MouseEventSource.MouseEventNotSynthesized  # source
    )
    preview_widget.wheelEvent(event)
    assert preview_widget._scale > initial_scale
    
    # 缩小
    event = QWheelEvent(
        pos,
        global_pos,
        QPoint(0, -120),
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
        Qt.MouseEventSource.MouseEventNotSynthesized
    )
    preview_widget.wheelEvent(event)
    assert preview_widget._scale == pytest.approx(initial_scale, abs=0.2)

def test_mouse_drag(qtbot, preview_widget, sample_image):
    """测试鼠标拖动"""
    # 设置一个较小的窗口尺寸
    preview_widget.resize(100, 100)
    preview_widget.setPixmap(sample_image)
    preview_widget._scale = 4.0  # 放大4倍以确保图片大于窗口
    preview_widget._update_scaled_pixmap()
    QTest.qWait(100)  # 等待更新
    
    print(f"\n图片尺寸: {preview_widget._scaled_pixmap.size()}")
    print(f"窗口尺寸: {preview_widget.size()}")
    print(f"最大可拖动范围: {max(0, (preview_widget._scaled_pixmap.width() - preview_widget.width()) // 2)}")
    
    initial_offset = QPoint(preview_widget._scroll_offset)
    print(f"初始偏移: {initial_offset}")
    
    # 开始拖动
    QTest.mousePress(preview_widget, Qt.MouseButton.LeftButton, pos=QPoint(50, 50))
    assert preview_widget._dragging
    assert preview_widget._drag_start == QPoint(50, 50)
    print(f"拖动起点: {preview_widget._drag_start}")
    
    # 移动鼠标（使用更大的移动距离）
    for i in range(5):
        move_pos = QPoint(60 + i*10, 60 + i*10)
        QTest.mouseMove(preview_widget, move_pos)
        QTest.qWait(50)  # 等待更新
        print(f"移动到: {move_pos}, 当前偏移: {preview_widget._scroll_offset}")
    
    print(f"最终偏移: {preview_widget._scroll_offset}")
    assert preview_widget._scroll_offset != initial_offset, "拖动后偏移量应该发生变化"
    
    # 释放鼠标
    QTest.mouseRelease(preview_widget, Qt.MouseButton.LeftButton)
    assert not preview_widget._dragging

def test_fit_to_view(preview_widget, sample_image):
    """测试适应窗口"""
    preview_widget.resize(200, 200)
    preview_widget.setPixmap(sample_image)
    
    # 执行适应窗口
    preview_widget.fit_to_view()
    QTest.qWait(100)  # 等待更新
    
    # 验证缩放比例（考虑边框和内边距）
    expected_scale = min(
        (preview_widget.width() - 2) / sample_image.width(),
        (preview_widget.height() - 2) / sample_image.height()
    )
    assert preview_widget._scale == pytest.approx(expected_scale, abs=0.1)
    assert preview_widget._scroll_offset == QPoint(0, 0)

def test_reset_view(preview_widget, sample_image):
    """测试重置视图"""
    preview_widget.setPixmap(sample_image)
    
    # 先缩放和移动
    preview_widget._scale = 2.0
    preview_widget._scroll_offset = QPoint(50, 50)
    preview_widget._update_scaled_pixmap()
    
    # 重置视图
    preview_widget.reset_view()
    QTest.qWait(100)  # 等待更新
    
    # 验证重置结果
    assert preview_widget._scale == 1.0
    assert preview_widget._scroll_offset == QPoint(0, 0)

def test_scale_limits(qtbot, preview_widget, sample_image):
    """测试缩放限制"""
    preview_widget.setPixmap(sample_image)
    
    pos = QPointF(100, 100)
    global_pos = QPointF(preview_widget.mapToGlobal(QPoint(100, 100)))
    
    # 测试最小缩放
    for _ in range(50):
        event = QWheelEvent(
            pos,
            global_pos,
            QPoint(0, -120),
            QPoint(0, -120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False,
            Qt.MouseEventSource.MouseEventNotSynthesized
        )
        preview_widget.wheelEvent(event)
    QTest.qWait(100)
    assert preview_widget._scale >= preview_widget._min_scale
    
    # 测试最大缩放
    for _ in range(50):
        event = QWheelEvent(
            pos,
            global_pos,
            QPoint(0, 120),
            QPoint(0, 120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False,
            Qt.MouseEventSource.MouseEventNotSynthesized
        )
        preview_widget.wheelEvent(event)
    QTest.qWait(100)
    assert preview_widget._scale <= preview_widget._max_scale

def test_drag_limits(qtbot, preview_widget, sample_image):
    """测试拖动限制"""
    preview_widget.resize(200, 200)
    preview_widget.setPixmap(sample_image)
    preview_widget._scale = 2.0
    preview_widget._update_scaled_pixmap()
    QTest.qWait(100)  # 等待更新
    
    # 开始拖动
    QTest.mousePress(preview_widget, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
    
    # 模拟多次小幅度拖动
    for i in range(10):
        QTest.mouseMove(preview_widget, QPoint(105 + i*2, 105 + i*2))
        QTest.qWait(20)  # 增加等待时间
    
    # 验证是否在限制范围内
    max_x = max(0, (preview_widget._scaled_pixmap.width() - preview_widget.width()) // 2)
    max_y = max(0, (preview_widget._scaled_pixmap.height() - preview_widget.height()) // 2)
    
    # 验证偏移量不超过最大值
    x_offset = preview_widget._scroll_offset.x()
    y_offset = preview_widget._scroll_offset.y()
    
    assert abs(x_offset) <= max_x + 1, f"X offset {x_offset} exceeds limit {max_x}"
    assert abs(y_offset) <= max_y + 1, f"Y offset {y_offset} exceeds limit {max_y}"
    
    # 释放鼠标
    QTest.mouseRelease(preview_widget, Qt.MouseButton.LeftButton) 
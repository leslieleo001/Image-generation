import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QImage, QWheelEvent
from PyQt6.QtCore import Qt, QPoint, QSize, QPointF
from src.ui.image_preview import ImagePreviewWidget
from PyQt6.QtTest import QTest
from pathlib import Path

@pytest.fixture
def preview_widget(qtbot):
    """创建预览组件"""
    widget = ImagePreviewWidget()
    qtbot.addWidget(widget)
    return widget

@pytest.fixture
def sample_image(tmp_path):
    """创建测试图片"""
    image = QImage(100, 100, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.white)
    pixmap = QPixmap.fromImage(image)
    
    # 保存为临时文件
    image_path = tmp_path / "test.png"
    pixmap.save(str(image_path))
    return str(image_path)

def test_init(preview_widget):
    """测试初始化"""
    assert preview_widget.minimumSize() == QSize(100, 100)
    assert preview_widget._scale == 1.0
    assert preview_widget._min_scale == 0.1
    assert preview_widget._max_scale == 5.0
    assert not preview_widget._dragging
    assert preview_widget._scroll_offset == QPoint(0, 0)
    assert len(preview_widget._pixmaps) == 0

def test_load_images(preview_widget, sample_image):
    """测试加载图片"""
    # 设置一个固定的窗口大小，避免自动缩放的影响
    preview_widget.resize(400, 400)
    preview_widget.load_images([sample_image])
    
    assert len(preview_widget._pixmaps) == 1
    assert preview_widget._current_index == 0
    assert preview_widget._scaled_pixmap is not None
    
    # 由于 load_images 会调用 fit_to_view，我们验证缩放比例是合理的
    assert 0.1 <= preview_widget._scale <= 5.0
    assert preview_widget._scroll_offset == QPoint(0, 0)

def test_wheel_zoom(qtbot, preview_widget, sample_image):
    """测试滚轮缩放"""
    preview_widget.load_images([sample_image])
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
    # 设置一个固定的窗口大小
    preview_widget.resize(200, 200)
    preview_widget.load_images([sample_image])
    
    # 禁用自动缩放
    preview_widget._scale = 2.0
    preview_widget._update_scaled_pixmap()
    QTest.qWait(100)  # 等待更新
    
    initial_offset = QPoint(preview_widget._scroll_offset)
    
    # 在图片标签上进行拖动
    label_pos = preview_widget.image_label.pos()
    start_pos = label_pos + QPoint(50, 50)
    
    # 开始拖动
    QTest.mousePress(preview_widget.image_label, Qt.MouseButton.LeftButton, pos=QPoint(50, 50))
    assert preview_widget._dragging
    assert preview_widget._drag_start == QPoint(50, 50)
    
    # 移动鼠标（使用更大的移动距离）
    for i in range(5):
        move_pos = QPoint(60 + i*20, 60 + i*20)  # 增加移动距离
        QTest.mouseMove(preview_widget.image_label, move_pos)
        QTest.qWait(50)  # 等待更新
    
    # 确保偏移量发生了变化
    assert preview_widget._scroll_offset != initial_offset, "拖动后偏移量应该发生变化"
    
    # 释放鼠标
    QTest.mouseRelease(preview_widget.image_label, Qt.MouseButton.LeftButton)

def test_fit_to_view(preview_widget, sample_image):
    """测试适应窗口"""
    preview_widget.load_images([sample_image])
    preview_widget.resize(200, 200)
    
    # 执行适应窗口
    preview_widget.fit_to_view()
    QTest.qWait(100)  # 等待更新
    
    # 验证缩放比例（考虑边框和内边距）
    expected_scale = min(
        (preview_widget.image_label.width() - 40) / preview_widget._pixmaps[0].width(),
        (preview_widget.image_label.height() - 40) / preview_widget._pixmaps[0].height()
    )
    # 确保缩放比例在允许的范围内
    expected_scale = max(preview_widget._min_scale, min(preview_widget._max_scale, expected_scale))
    assert preview_widget._scale == pytest.approx(expected_scale, abs=0.1)
    assert preview_widget._scroll_offset == QPoint(0, 0)

def test_reset_view(preview_widget, sample_image):
    """测试重置视图"""
    preview_widget.load_images([sample_image])
    
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
    preview_widget.load_images([sample_image])
    
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
    preview_widget.load_images([sample_image])
    preview_widget.resize(200, 200)
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
    max_x = max(0, (preview_widget._scaled_pixmap.width() - preview_widget.image_label.width()) // 2)
    max_y = max(0, (preview_widget._scaled_pixmap.height() - preview_widget.image_label.height()) // 2)
    
    # 验证偏移量不超过最大值
    x_offset = preview_widget._scroll_offset.x()
    y_offset = preview_widget._scroll_offset.y()
    
    assert abs(x_offset) <= max_x + 1, f"X offset {x_offset} exceeds limit {max_x}"
    assert abs(y_offset) <= max_y + 1, f"Y offset {y_offset} exceeds limit {max_y}"
    
    # 释放鼠标
    QTest.mouseRelease(preview_widget, Qt.MouseButton.LeftButton)

def test_navigation(preview_widget, tmp_path):
    """测试图片导航"""
    # 创建多个测试图片
    image_paths = []
    for i in range(3):
        image = QImage(100, 100, QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.white)
        pixmap = QPixmap.fromImage(image)
        path = tmp_path / f"test_{i}.png"
        pixmap.save(str(path))
        image_paths.append(str(path))
    
    # 加载图片
    preview_widget.load_images(image_paths)
    assert preview_widget._current_index == 0
    assert len(preview_widget._pixmaps) == 3
    
    # 测试下一张
    preview_widget.next_image()
    assert preview_widget._current_index == 1
    
    # 测试上一张
    preview_widget.previous_image()
    assert preview_widget._current_index == 0
    
    # 测试循环
    preview_widget.previous_image()
    assert preview_widget._current_index == 2 
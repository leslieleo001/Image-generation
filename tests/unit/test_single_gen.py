import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.ui.single_gen import SingleGenTab
from src.utils.api_manager import APIManager
from src.utils.config_manager import ConfigManager
import sys

@pytest.fixture
def app():
    """创建QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def single_gen_tab(app):
    """创建SingleGenTab实例"""
    config = ConfigManager()
    api_manager = APIManager(config)
    return SingleGenTab(api_manager, config)

def test_ui_initialization(single_gen_tab):
    """测试界面初始化"""
    # 测试基本控件是否存在
    assert single_gen_tab.prompt_input is not None
    assert single_gen_tab.negative_prompt is not None
    assert single_gen_tab.model_combo is not None
    assert single_gen_tab.size_combo is not None
    assert single_gen_tab.num_images_spin is not None
    assert single_gen_tab.steps_spin is not None
    assert single_gen_tab.guidance_spin is not None
    assert single_gen_tab.prompt_enhancement is not None
    assert single_gen_tab.seed_spin is not None
    assert single_gen_tab.random_seed is not None
    assert single_gen_tab.preview_label is not None
    assert single_gen_tab.thumbnails_list is not None
    assert single_gen_tab.history_list is not None

def test_input_fields_properties(single_gen_tab):
    """测试输入字段属性"""
    # 测试提示词输入框高度
    assert single_gen_tab.prompt_input.minimumHeight() == 60
    assert single_gen_tab.negative_prompt.minimumHeight() == 60
    
    # 测试生成数量范围
    assert single_gen_tab.num_images_spin.minimum() == 1
    assert single_gen_tab.num_images_spin.maximum() == 10
    assert single_gen_tab.num_images_spin.value() == 1

def test_layout_structure(single_gen_tab):
    """测试布局结构"""
    # 测试主要组件是否可见
    assert single_gen_tab.generate_btn.isVisible()
    assert single_gen_tab.manual_generate_btn.isVisible()
    assert single_gen_tab.save_btn.isVisible()
    assert not single_gen_tab.save_btn.isEnabled()  # 初始应该禁用

def test_thumbnail_functionality(single_gen_tab):
    """测试缩略图功能"""
    # 测试缩略图列表设置
    assert single_gen_tab.thumbnails_list.viewMode() == single_gen_tab.thumbnails_list.ViewMode.IconMode
    assert single_gen_tab.thumbnails_list.iconSize().width() == 100
    assert single_gen_tab.thumbnails_list.iconSize().height() == 100

def test_button_states(single_gen_tab):
    """测试按钮状态"""
    # 测试初始按钮状态
    assert single_gen_tab.generate_btn.isEnabled()
    assert single_gen_tab.manual_generate_btn.isEnabled()
    assert not single_gen_tab.save_btn.isEnabled()

def test_model_change_behavior(single_gen_tab):
    """测试模型切换行为"""
    # 测试切换到turbo模型
    turbo_model = "stabilityai/stable-diffusion-3-5-large-turbo"
    single_gen_tab.model_combo.setCurrentText(turbo_model)
    assert single_gen_tab.steps_spin.value() == 4
    assert not single_gen_tab.steps_spin.isEnabled()
    
    # 测试切换到非turbo模型
    normal_model = "stabilityai/stable-diffusion-3-5-large"
    single_gen_tab.model_combo.setCurrentText(normal_model)
    assert single_gen_tab.steps_spin.isEnabled()

def test_random_seed_behavior(single_gen_tab):
    """测试随机种子行为"""
    # 测试随机种子开关
    assert single_gen_tab.random_seed.isChecked()
    assert not single_gen_tab.seed_spin.isEnabled()
    
    # 关闭随机种子
    single_gen_tab.random_seed.setChecked(False)
    assert single_gen_tab.seed_spin.isEnabled()

def test_clear_thumbnails(single_gen_tab):
    """测试清空缩略图功能"""
    # 清空缩略图
    single_gen_tab.clear_thumbnails()
    assert single_gen_tab.thumbnails_list.count() == 0
    assert len(single_gen_tab.current_images) == 0
    assert single_gen_tab.current_image is None
    assert not single_gen_tab.save_btn.isEnabled()

def test_parameter_validation(single_gen_tab):
    """测试参数验证"""
    # 测试空提示词
    params = single_gen_tab.get_generation_params()
    with pytest.raises(ValueError, match="提示词不能为空"):
        single_gen_tab.validate_params(params)
    
    # 设置有效提示词
    single_gen_tab.prompt_input.setText("测试提示词")
    params = single_gen_tab.get_generation_params()
    single_gen_tab.validate_params(params)  # 不应该抛出异常 
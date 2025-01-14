import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest, QSignalSpy
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
    return SingleGenTab(config, api_manager)

def test_ui_initialization(single_gen_tab):
    """测试界面初始化"""
    # 测试基本控件是否存在
    assert single_gen_tab.prompt_input is not None
    assert single_gen_tab.negative_input is not None
    assert single_gen_tab.model_combo is not None
    assert single_gen_tab.size_combo is not None
    assert single_gen_tab.batch_spin is not None
    assert single_gen_tab.steps_spin is not None
    assert single_gen_tab.guidance_spin is not None
    assert single_gen_tab.enhance_check is not None
    assert single_gen_tab.seed_input is not None
    assert single_gen_tab.random_seed_check is not None
    assert single_gen_tab.history_list is not None

def test_input_fields_properties(single_gen_tab):
    """测试输入字段属性"""
    # 测试提示词输入框高度
    assert single_gen_tab.prompt_input.maximumHeight() == 100
    assert single_gen_tab.negative_input.maximumHeight() == 100
    
    # 测试生成数量范围
    assert single_gen_tab.batch_spin.minimum() == 1
    assert single_gen_tab.batch_spin.maximum() == 4
    assert single_gen_tab.batch_spin.value() == 1

def test_layout_structure(single_gen_tab):
    """测试布局结构"""
    # 测试主要组件是否存在
    assert single_gen_tab.generate_btn is not None
    assert single_gen_tab.progress_label is not None
    assert single_gen_tab.history_list is not None

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
    # 创建信号监听器
    spy = QSignalSpy(single_gen_tab.random_seed_check.stateChanged)
    
    # 测试随机种子开关
    assert not single_gen_tab.random_seed_check.isChecked()  # 默认不选中
    assert single_gen_tab.seed_input.isEnabled()  # 种子值输入框可用
    
    # 选中随机种子
    single_gen_tab.random_seed_check.setChecked(True)
    assert len(spy) > 0  # 确保信号被触发
    assert not single_gen_tab.seed_input.isEnabled()  # 种子值输入框禁用
    assert single_gen_tab.seed_input.text() == ""  # 种子值清空
    
    # 取消随机种子
    single_gen_tab.random_seed_check.setChecked(False)
    assert len(spy) > 1  # 确保信号被触发
    assert single_gen_tab.seed_input.isEnabled()  # 种子值输入框可用

def test_parameter_validation(single_gen_tab):
    """测试参数验证"""
    # 获取参数
    params = single_gen_tab.get_generation_params()
    
    # 验证必要参数存在
    assert "prompt" in params
    assert "model" in params
    assert "size" in params
    assert "num_inference_steps" in params
    assert "guidance_scale" in params
    assert "batch_size" in params
    
    # 验证参数值
    assert params["batch_size"] >= 1
    assert params["batch_size"] <= 4
    assert params["num_inference_steps"] >= 1
    assert params["num_inference_steps"] <= 50
    assert params["guidance_scale"] >= 0
    assert params["guidance_scale"] <= 20

def test_random_seed_functionality(single_gen_tab):
    """测试随机种子功能"""
    # 创建信号监听器
    spy = QSignalSpy(single_gen_tab.random_seed_check.stateChanged)
    
    # 验证初始状态
    assert not single_gen_tab.random_seed_check.isChecked()  # 默认不选中
    assert single_gen_tab.seed_input.isEnabled()  # 种子值输入框可用
    
    # 测试选中随机种子
    single_gen_tab.random_seed_check.setChecked(True)
    assert len(spy) > 0  # 确保信号被触发
    assert single_gen_tab.random_seed_check.isChecked()  # 选中状态
    assert not single_gen_tab.seed_input.isEnabled()  # 种子值输入框禁用
    assert single_gen_tab.seed_input.text() == ""  # 种子值清空
    
    # 测试取消随机种子
    single_gen_tab.random_seed_check.setChecked(False)
    assert len(spy) > 1  # 确保信号被触发
    assert not single_gen_tab.random_seed_check.isChecked()  # 取消选中
    assert single_gen_tab.seed_input.isEnabled()  # 种子值输入框可用
    
    # 测试参数获取
    # 1. 使用随机种子
    single_gen_tab.random_seed_check.setChecked(True)
    assert len(spy) > 2  # 确保信号被触发
    params = single_gen_tab.get_generation_params()
    assert "seed" in params
    assert isinstance(params["seed"], int)
    assert 1 <= params["seed"] <= 9999999998
    
    # 2. 使用固定种子值
    single_gen_tab.random_seed_check.setChecked(False)
    assert len(spy) > 3  # 确保信号被触发
    single_gen_tab.seed_input.setText("42")
    params = single_gen_tab.get_generation_params()
    assert params["seed"] == 42
    
    # 3. 种子值为空
    single_gen_tab.seed_input.clear()
    params = single_gen_tab.get_generation_params()
    assert "seed" in params
    assert isinstance(params["seed"], int)
    assert 1 <= params["seed"] <= 9999999998 
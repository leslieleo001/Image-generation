import pytest
import pandas as pd
from pathlib import Path
from src.utils.excel_handler import ExcelHandler, GenerationTask
import os

@pytest.fixture
def sample_excel(tmp_path):
    """创建示例Excel文件"""
    file_path = tmp_path / "sample.xlsx"
    df = pd.DataFrame({
        "提示词": ["测试1", "测试2"],
        "模型": ["模型A", "模型B"],
        "尺寸": ["512x512", "1024x1024"]
    })
    df.to_excel(file_path, index=False)
    return str(file_path)

@pytest.fixture
def invalid_excel(tmp_path):
    """创建格式错误的Excel文件"""
    file_path = tmp_path / "invalid.xlsx"
    data = {
        "错误列1": ["数据1"],
        "错误列2": ["数据2"]
    }
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)
    return str(file_path)

def test_read_tasks(sample_excel):
    """测试从Excel文件读取任务"""
    tasks = ExcelHandler.read_tasks(sample_excel)
    assert len(tasks) == 2
    
    # 验证第一个任务
    assert tasks[0].prompt == "测试1"
    assert tasks[0].model == "模型A"
    assert tasks[0].size == "512x512"
    assert tasks[0].status == "等待中"
    assert tasks[0].result_path is None
    
    # 验证第二个任务
    assert tasks[1].prompt == "测试2"
    assert tasks[1].model == "模型B"
    assert tasks[1].size == "1024x1024"
    assert tasks[1].status == "等待中"
    assert tasks[1].result_path is None

def test_read_tasks_invalid_file(invalid_excel):
    """测试读取格式错误的文件"""
    with pytest.raises(ValueError) as exc_info:
        ExcelHandler.read_tasks(invalid_excel)
    assert "缺少必需列" in str(exc_info.value)

def test_read_tasks_file_not_found():
    """测试读取不存在的文件"""
    with pytest.raises(FileNotFoundError) as exc_info:
        ExcelHandler.read_tasks("not_exist.xlsx")
    assert "文件不存在" in str(exc_info.value)

def test_export_results(tmp_path):
    """测试导出任务结果到Excel文件"""
    # 创建测试任务
    tasks = [
        GenerationTask(prompt="测试1", model="模型1", size="1024x1024"),
        GenerationTask(prompt="测试2", model="模型2", size="512x512")
    ]
    
    # 设置任务状态
    tasks[0].status = "完成"
    tasks[1].status = "等待中"
    
    # 导出文件路径
    file_path = str(tmp_path / "export.xlsx")
    
    # 导出结果
    ExcelHandler.export_results(tasks, file_path)
    
    # 验证文件存在
    assert os.path.exists(file_path)
    
    try:
        # 读取并验证内容
        df = pd.read_excel(file_path)
        assert len(df) == 2
        
        # 验证列名
        expected_columns = ["提示词", "模型", "尺寸", "状态", "结果路径"]
        assert list(df.columns) == expected_columns
        
        # 验证数据
        assert df.iloc[0]["提示词"] == "测试1"
        assert df.iloc[0]["模型"] == "模型1"
        assert df.iloc[0]["尺寸"] == "1024x1024"
        assert df.iloc[0]["状态"] == "完成"
        
        assert df.iloc[1]["提示词"] == "测试2"
        assert df.iloc[1]["模型"] == "模型2"
        assert df.iloc[1]["尺寸"] == "512x512"
        assert df.iloc[1]["状态"] == "等待中"
    except Exception as e:
        pytest.fail(f"验证导出结果失败: {str(e)}")

def test_create_template(tmp_path):
    """测试创建模板"""
    file_path = tmp_path / "template.xlsx"
    ExcelHandler.create_template(file_path)
    
    # 验证模板文件
    df = pd.read_excel(file_path)
    assert len(df) == 2
    assert "提示词" in df.columns
    assert "模型" in df.columns
    assert "尺寸" in df.columns
    assert df.iloc[0]["提示词"] == "示例提示词1"
    assert df.iloc[0]["模型"] == "模型A"
    assert df.iloc[0]["尺寸"] == "1024x1024" 
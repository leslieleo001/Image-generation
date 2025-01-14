import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
from src.models.generation_task import GenerationTask

class ExcelHandler:
    """Excel文件处理类"""
    
    REQUIRED_COLUMNS = ["提示词", "模型", "尺寸"]
    
    @staticmethod
    def read_tasks(file_path: str) -> list:
        """从Excel文件读取任务列表
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            list: 任务列表
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
        """
        try:
            df = pd.read_excel(file_path)
            
            # 检查必需列
            missing_columns = [col for col in ExcelHandler.REQUIRED_COLUMNS if col not in df.columns]
            if missing_columns:
                raise ValueError(f"缺少必需列: {', '.join(missing_columns)}")
            
            # 读取任务
            tasks = []
            for _, row in df.iterrows():
                task = GenerationTask(
                    prompt=str(row["提示词"]).strip(),
                    model=str(row["模型"]).strip(),
                    size=str(row["尺寸"]).strip()
                )
                tasks.append(task)
            
            return tasks
            
        except FileNotFoundError:
            raise FileNotFoundError("文件不存在")
        except Exception as e:
            raise ValueError(f"文件格式错误: {str(e)}")
    
    @staticmethod
    def export_results(tasks: list, file_path: str) -> None:
        """导出任务结果到Excel文件
        
        Args:
            tasks: 任务列表
            file_path: 导出文件路径
            
        Raises:
            ValueError: 导出失败
        """
        try:
            # 准备数据
            data = []
            for task in tasks:
                data.append({
                    "提示词": str(task.prompt),
                    "模型": str(task.model),
                    "尺寸": str(task.size),
                    "状态": str(task.status),
                    "结果路径": str(task.result_path) if task.result_path else ""
                })
            
            # 创建 DataFrame 并导出
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            
        except Exception as e:
            raise ValueError(f"导出失败: {str(e)}")
    
    @staticmethod
    def create_template(file_path: str) -> None:
        """创建模板Excel文件
        
        Args:
            file_path: 模板文件路径
            
        Raises:
            ValueError: 创建失败
        """
        try:
            data = {
                "提示词": ["示例提示词1", "示例提示词2"],
                "模型": ["模型A", "模型B"],
                "尺寸": ["1024x1024", "512x512"]
            }
            df = pd.DataFrame(data)
            df.to_excel(str(file_path), index=False)
            
        except Exception as e:
            raise ValueError(f"创建模板失败: {str(e)}") 
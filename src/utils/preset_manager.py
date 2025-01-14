import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from .config_manager import ConfigManager

class PresetManager:
    def __init__(self, config: ConfigManager):
        """初始化预设管理器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.presets_dir = Path(config.get("paths.presets_dir", "presets"))
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        self._presets = {}
        self.load_presets()
    
    def load_presets(self) -> None:
        """加载所有预设"""
        try:
            for preset_file in self.presets_dir.glob("*.json"):
                with open(preset_file, "r", encoding="utf-8") as f:
                    preset = json.load(f)
                    if isinstance(preset, dict) and "name" in preset and "params" in preset:
                        self._presets[preset["name"]] = preset
        except Exception as e:
            print(f"加载预设失败: {e}")
    
    def save_preset(self, name: str, params: dict) -> bool:
        """保存预设
        Args:
            name: 预设名称
            params: 参数字典
        Returns:
            bool: 是否保存成功
        """
        try:
            preset = {
                "name": name,
                "params": params,
                "description": params.get("description", "")
            }
            
            # 验证预设目录是否可写
            if not os.access(self.presets_dir, os.W_OK):
                print("预设目录不可写")
                return False
            
            file_path = self.presets_dir / f"{name}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(preset, f, ensure_ascii=False, indent=2)
            
            self._presets[name] = preset
            return True
        except Exception as e:
            print(f"保存预设失败: {e}")
            return False
    
    def get_preset(self, name: str) -> Optional[dict]:
        """获取预设
        Args:
            name: 预设名称
        Returns:
            dict: 预设参数，如果不存在则返回None
        """
        preset = self._presets.get(name)
        return preset["params"] if preset else None
    
    def list_presets(self) -> List[Dict]:
        """获取所有预设列表
        Returns:
            List[Dict]: 预设列表
        """
        return list(self._presets.values())
    
    def delete_preset(self, name: str) -> bool:
        """删除预设
        Args:
            name: 预设名称
        Returns:
            bool: 是否删除成功
        """
        try:
            if name in self._presets:
                file_path = self.presets_dir / f"{name}.json"
                if file_path.exists():
                    file_path.unlink()
                del self._presets[name]
                return True
            return False
        except Exception as e:
            print(f"删除预设失败: {e}")
            return False
    
    def update_preset(self, name: str, params: dict) -> bool:
        """更新预设
        Args:
            name: 预设名称
            params: 新的参数字典
        Returns:
            bool: 是否更新成功
        """
        if name not in self._presets:
            return False
        return self.save_preset(name, params)
    
    def import_presets(self, file_path: str) -> bool:
        """导入预设
        Args:
            file_path: 预设文件路径
        Returns:
            bool: 是否导入成功
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                presets = json.load(f)
            
            if not isinstance(presets, list):
                presets = [presets]
            
            success = True
            for preset in presets:
                if isinstance(preset, dict) and "name" in preset and "params" in preset:
                    if not self.save_preset(preset["name"], preset["params"]):
                        success = False
            return success
        except Exception as e:
            print(f"导入预设失败: {e}")
            return False
    
    def export_presets(self, file_path: str, preset_names: Optional[List[str]] = None) -> bool:
        """导出预设
        Args:
            file_path: 导出文件路径
            preset_names: 要导出的预设名称列表,为None时导出所有
        Returns:
            bool: 是否导出成功
        """
        try:
            # 验证导出目录是否可写
            export_dir = os.path.dirname(file_path)
            if not os.access(export_dir, os.W_OK):
                print("导出目录不可写")
                return False
            
            if preset_names is None:
                presets = list(self._presets.values())
            else:
                presets = [self._presets[name] for name in preset_names if name in self._presets]
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(presets, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出预设失败: {e}")
            return False 
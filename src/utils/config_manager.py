import json
import os
from typing import Dict, Any
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / '.image_generator'
        self.config_file = self.config_dir / 'config.json'
        self.defaults = {
            "models": [
                "stabilityai/stable-diffusion-3-5-large",
                "stabilityai/stable-diffusion-3-medium",
                "stabilityai/stable-diffusion-3-5-large-turbo"
            ],
            "defaults": {
                "size": "512x512",
                "steps": 20,
                "guidance": 7.5,
                "seed": -1,
                "enhance": False
            },
            "paths": {
                "output_dir": "",
                "presets_dir": "presets",
                "history_file": "history.json"
            },
            "history": {
                "max_items": 100
            },
            "naming_rule": {
                "preset": "默认",
                "custom": "{timestamp}_{prompt}_{model}_{size}_{seed}"
            }
        }
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            # 确保配置目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置，确保新添加的配置项存在
                return self._merge_configs(self.defaults, config)
            else:
                self.save_config(self.defaults)
                return self.defaults
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self.defaults
            
    def save_config(self, config=None):
        """保存配置文件"""
        try:
            if config is None:
                config = self.config
            
            # 确保配置目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            self.config = config
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        try:
            # 使用点号分隔的键获取嵌套配置
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any) -> bool:
        """设置配置项"""
        try:
            # 使用点号分隔的键设置嵌套配置
            keys = key.split('.')
            config = self.config
            
            # 遍历到最后一个键之前
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
                
            # 设置最后一个键的值
            config[keys[-1]] = value
            return True
        except Exception as e:
            print(f"设置配置项失败: {e}")
            return False
            
    def _merge_configs(self, default: Dict, config: Dict) -> Dict:
        """合并配置，确保所有默认配置项都存在"""
        result = default.copy()
        
        def merge_dict(target, source):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    merge_dict(target[key], value)
                else:
                    target[key] = value
                    
        merge_dict(result, config)
        return result 
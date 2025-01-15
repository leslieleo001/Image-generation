import json
import os
import sys
import logging
from typing import Dict, Any
from pathlib import Path

class ConfigManager:
    def __init__(self):
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 获取程序运行目录
        if getattr(sys, 'frozen', False):
            # 如果是打包后的 exe
            self.project_root = Path(os.path.dirname(sys.executable))
            self.logger.info(f"使用打包模式，程序根目录: {self.project_root}")
        else:
            # 如果是源码运行，使用当前工作目录
            self.project_root = Path.cwd()
            self.logger.info(f"使用开发模式，程序根目录: {self.project_root}")
        
        # 配置文件路径（在程序运行目录下）
        self.config_dir = self.project_root / 'config'
        self.config_file = self.config_dir / 'config.json'
        
        self.defaults = {
            "api_key": "",
            "models": [
                "stabilityai/stable-diffusion-3-5-large",
                "stabilityai/stable-diffusion-3-medium",
                "stabilityai/stable-diffusion-3-5-large-turbo"
            ],
            "defaults": {
                "model": "stabilityai/stable-diffusion-3-5-large",
                "size": "1024x1024",
                "steps": 20,
                "guidance": 7.5,
                "enhance": False,
                "negative_prompt": "",
                "batch_size": 1,
                "seed": -1,
                "use_random_seed": True
            },
            "paths": {
                "output_dir": str(self.project_root / "output"),
                "presets_dir": str(self.project_root / "presets"),
                "history_file": str(self.project_root / "history" / "history.json")
            },
            "history": {
                "max_items": 100
            },
            "naming_rule": {
                "preset": "{date}_{prompt}_{index}_{seed}",
                "custom": "{date}_{prompt}_{index}_{seed}",
                "presets": [
                    "{date}_{prompt}_{index}_{seed}",
                    "{timestamp}_{prompt}_{model}_{size}_{seed}",
                    "{date}_{time}_{prompt}_{model}_{size}",
                    "自定义规则"
                ]
            }
        }
        
        # 确保所有必要的目录存在
        if not self._ensure_directories():
            raise RuntimeError("无法创建必要的目录，请检查程序权限")
        
        # 加载配置
        self.config = self.load_config()
        
    def _ensure_directories(self) -> bool:
        """确保所有必要的目录存在"""
        directories = [
            self.config_dir,
            Path(self.defaults["paths"]["output_dir"]),
            Path(self.defaults["paths"]["presets_dir"]),
            Path(self.defaults["paths"]["history_file"]).parent
        ]
        
        try:
            for directory in directories:
                try:
                    # 尝试创建目录
                    os.makedirs(directory, exist_ok=True)
                    
                    # 测试目录是否可写
                    test_file = directory / ".write_test"
                    test_file.touch()
                    test_file.unlink()
                    
                    self.logger.info(f"成功创建并验证目录: {directory}")
                except Exception as e:
                    self.logger.error(f"创建或验证目录失败: {directory}, 错误: {e}")
                    return False
            return True
            
        except Exception as e:
            self.logger.error(f"创建目录时发生错误: {e}")
            return False
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    # 合并默认配置，确保新添加的配置项存在
                    merged_config = self._merge_configs(self.defaults, config)
                    self.logger.info("成功加载配置文件")
                    return merged_config
                except json.JSONDecodeError as e:
                    self.logger.error(f"配置文件格式错误: {e}")
                    # 备份损坏的配置文件
                    backup_file = self.config_file.with_suffix('.json.bak')
                    os.rename(self.config_file, backup_file)
                    self.logger.info(f"已备份损坏的配置文件到: {backup_file}")
            
            # 如果配置文件不存在或已损坏，创建新的配置文件
            self.save_config(self.defaults)
            self.logger.info("已创建新的配置文件")
            return self.defaults
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return self.defaults
            
    def save_config(self, config=None) -> bool:
        """保存配置文件"""
        if config is None:
            config = self.config
            
        try:
            # 确保配置目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            # 先将配置写入临时文件
            temp_file = self.config_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 如果写入成功，替换原文件
            if os.path.exists(self.config_file):
                os.replace(temp_file, self.config_file)
            else:
                os.rename(temp_file, self.config_file)
            
            self.config = config
            self.logger.info("成功保存配置文件")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        try:
            # 使用点号分隔的键获取嵌套配置
            keys = key.split('.')
            value = self.config
            for k in keys:
                if k not in value:
                    return default
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
            
            # 立即保存配置
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"设置配置项失败: {e}")
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
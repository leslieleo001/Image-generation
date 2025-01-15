import os
import sys
import logging
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.config_manager import ConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_packaged.log')
    ]
)
logger = logging.getLogger(__name__)

def simulate_packaged_env():
    """模拟打包后的环境"""
    try:
        logger.info("开始模拟打包环境")
        # 设置 frozen 属性来模拟打包环境
        setattr(sys, 'frozen', True)
        # 设置可执行文件路径为当前目录
        executable_path = str(Path.cwd() / "Silicon Flow.exe")
        sys.executable = executable_path
        logger.info(f"设置可执行文件路径为: {executable_path}")
    except Exception as e:
        logger.error(f"模拟打包环境失败: {e}")
        logger.error(traceback.format_exc())
        raise

def cleanup_test_files():
    """清理测试文件"""
    try:
        logger.info("开始清理测试文件")
        test_dirs = ['config', 'output', 'presets', 'history']
        for dir_name in test_dirs:
            path = Path.cwd() / dir_name
            if path.exists():
                logger.info(f"删除目录: {path}")
                os.system(f'rd /s /q "{path}"')
                if path.exists():
                    logger.warning(f"目录删除失败: {path}")
    except Exception as e:
        logger.error(f"清理测试文件失败: {e}")
        logger.error(traceback.format_exc())

def test_directory_permissions():
    """测试目录权限"""
    try:
        logger.info("测试目录权限")
        test_dirs = ['config', 'output', 'presets', 'history']
        for dir_name in test_dirs:
            path = Path.cwd() / dir_name
            try:
                # 尝试创建目录
                path.mkdir(parents=True, exist_ok=True)
                # 尝试创建测试文件
                test_file = path / "test.txt"
                test_file.write_text("test")
                test_file.unlink()
                logger.info(f"目录权限正常: {path}")
            except Exception as e:
                logger.error(f"目录权限测试失败: {path}")
                logger.error(str(e))
                return False
        return True
    except Exception as e:
        logger.error(f"权限测试过程出错: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    try:
        logger.info("=== 开始测试 ===")
        
        # 清理之前的测试文件
        cleanup_test_files()
        
        # 测试目录权限
        if not test_directory_permissions():
            logger.error("目录权限测试失败，请检查程序权限")
            return False
        
        # 模拟打包环境
        simulate_packaged_env()
        
        # 创建配置管理器
        logger.info("创建配置管理器")
        config_manager = ConfigManager()
        
        logger.info("=== 配置管理器信息 ===")
        logger.info(f"项目根目录: {config_manager.project_root}")
        logger.info(f"配置目录: {config_manager.config_dir}")
        logger.info(f"配置文件: {config_manager.config_file}")
        
        # 测试保存配置
        test_config = {
            "api_key": "test_key_789",
            "defaults": {
                "model": "test_model",
                "size": "512x512"
            }
        }
        
        logger.info("测试保存配置")
        if config_manager.save_config(test_config):
            logger.info("配置保存成功")
        else:
            logger.error("配置保存失败")
            return False
        
        # 验证目录是否创建
        logger.info("=== 验证目录创建 ===")
        directories = [
            config_manager.config_dir,
            Path(config_manager.defaults["paths"]["output_dir"]),
            Path(config_manager.defaults["paths"]["presets_dir"]),
            Path(config_manager.defaults["paths"]["history_file"]).parent
        ]
        
        all_dirs_exist = True
        for directory in directories:
            if directory.exists():
                logger.info(f"目录已创建: {directory}")
                # 测试目录权限
                try:
                    test_file = directory / "test.txt"
                    test_file.write_text("test")
                    test_file.unlink()
                    logger.info(f"目录可写: {directory}")
                except Exception as e:
                    logger.error(f"目录权限不足: {directory}")
                    logger.error(str(e))
                    all_dirs_exist = False
            else:
                logger.error(f"目录创建失败: {directory}")
                all_dirs_exist = False
        
        if not all_dirs_exist:
            return False
        
        # 测试配置加载
        logger.info("=== 测试配置加载 ===")
        new_config_manager = ConfigManager()
        loaded_api_key = new_config_manager.get("api_key")
        logger.info(f"加载的API密钥: {loaded_api_key}")
        
        if loaded_api_key == "test_key_789":
            logger.info("配置加载成功")
        else:
            logger.error("配置加载失败")
            return False
        
        logger.info("=== 测试完成 ===")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    try:
        success = main()
        logger.info(f"\n测试{'成功' if success else '失败'}")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1) 
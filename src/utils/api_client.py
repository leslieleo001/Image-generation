import requests
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from datetime import datetime

class APIError(Exception):
    """API错误基类"""
    def __init__(self, message: str, code: Optional[int] = None, data: Any = None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)

class SiliconFlowAPI:
    def __init__(self, api_key: str, base_url: str = "https://api.siliconflow.cn/v1", proxy: Optional[Dict] = None):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            proxy: 代理设置，格式如 {"http": "http://proxy:port", "https": "https://proxy:port"}
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if proxy:
            self.session.proxies.update(proxy)
        
        # 设置默认请求头
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",  # 添加Bearer前缀
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # 设置日志
        self.logger = logging.getLogger("SiliconFlowAPI")
        # 确保日志器有处理器
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)  # 设置为DEBUG级别以显示详细信息
    
    def generate_image(self, 
                      prompt: str,
                      model: str = "stabilityai/stable-diffusion-3-5-large",
                      negative_prompt: str = "",
                      size: str = "1024x1024",
                      batch_size: int = 1,
                      seed: Optional[int] = None,
                      num_inference_steps: int = 20,
                      guidance_scale: float = 7.5,
                      prompt_enhancement: bool = False) -> Dict[str, Any]:
        """
        生成图片
        
        Args:
            prompt: 提示词
            model: 模型名称
            negative_prompt: 负面提示词
            size: 图片尺寸
            batch_size: 批量生成数量 (1-4)
            seed: 随机种子 (0-2147483647)
            num_inference_steps: 推理步数 (1-50，turbo模型固定为4)
            guidance_scale: 引导系数 (0-20)
            prompt_enhancement: 提示增强
            
        Returns:
            Dict: API响应数据，包含图片URL等信息
        """
        # 验证参数
        if not prompt.strip():
            raise ValueError("提示词不能为空")
            
        if not (0 <= guidance_scale <= 20):
            raise ValueError("引导系数必须在0到20之间")
            
        if not (1 <= batch_size <= 4):
            raise ValueError("生成数量必须在1到4之间")
            
        if not (1 <= num_inference_steps <= 50):
            raise ValueError("生成步数必须在1到50之间")
            
        if seed is not None and not (0 <= seed <= 2147483647):
            raise ValueError("种子值必须在0到2147483647之间")
            
        # 对于turbo模型，强制使用4步
        if "turbo" in model.lower():
            num_inference_steps = 4
            self.logger.info("turbo模型已自动设置为4步")
        
        payload = {
            "model": model,
            "prompt": prompt.strip(),
            "negative_prompt": negative_prompt.strip(),
            "image_size": size,  # 修改参数名为image_size
            "batch_size": batch_size,  # 使用batch_size
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "prompt_enhancement": prompt_enhancement
        }
        
        if seed is not None:
            payload["seed"] = seed
            
        try:
            self.logger.debug(f"发送请求到 {self.base_url}/images/generations")
            self.logger.debug(f"请求参数: {payload}")
            
            response = self.session.post(
                f"{self.base_url}/images/generations",
                json=payload
            )
            
            # 检查响应状态码
            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"API响应成功: {result}")
                return result
            
            # 尝试解析错误信息
            try:
                error_data = response.json()
                error_message = error_data.get('message', response.text)
            except:
                error_message = response.text
            
            self.logger.error(f"API请求失败: {error_message}")
            
            # 根据状态码返回特定错误
            if response.status_code == 401:
                raise APIError("API密钥无效", 401)
            elif response.status_code == 429:
                raise APIError("超出请求限制，如需更多额度请联系 contact@siliconflow.cn", 429)
            elif response.status_code == 503:
                raise APIError("服务暂时不可用，请稍后重试", 503)
            else:
                raise APIError(f"API请求失败: {error_message}", response.status_code)
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"网络请求失败: {str(e)}")
            raise APIError(f"网络请求失败: {str(e)}")
    
    def download_image(self, url: str, save_path: Path) -> Path:
        """
        下载生成的图片
        
        Args:
            url: 图片URL
            save_path: 保存路径
            
        Returns:
            Path: 保存的文件路径
            
        Raises:
            APIError: 下载失败时抛出
        """
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # 确保保存目录存在
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return save_path
            
        except Exception as e:
            raise APIError(f"图片下载失败: {str(e)}")
    
    def validate_api_key(self) -> bool:
        """
        验证API密钥是否有效
        
        Returns:
            bool: 密钥是否有效
        """
        try:
            self.logger.debug(f"正在验证API密钥，请求URL: {self.base_url}/models")
            self.logger.debug(f"请求头: {self.session.headers}")
            
            response = self.session.get(f"{self.base_url}/models")
            
            self.logger.debug(f"收到响应，状态码: {response.status_code}")
            
            # 检查响应状态码
            if response.status_code == 200:
                self.logger.info("API密钥验证成功")
                return True
            elif response.status_code == 401:
                self.logger.warning("API密钥无效")
                return False
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', response.text)
                except:
                    error_message = response.text
                self.logger.error(f"API请求失败: {error_message}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"网络请求失败: {str(e)}")
            return False 
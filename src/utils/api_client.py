import requests
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from datetime import datetime
import time

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
        self.session.headers.update(self._get_headers())
        
        # 设置日志
        self.logger = logging.getLogger("SiliconFlowAPI")
        # 确保日志器有处理器
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)  # 设置为DEBUG级别以显示详细信息
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def generate_image(self, prompt, model, negative_prompt="", size="1024x1024", 
                      batch_size=1, num_inference_steps=20, guidance_scale=7.5, 
                      prompt_enhancement=False, seeds=None, max_retries=3):
        """
        生成图片
        :param prompt: 提示词
        :param model: 模型名称
        :param negative_prompt: 负面提示词
        :param size: 图片尺寸
        :param batch_size: 生成数量
        :param num_inference_steps: 生成步数
        :param guidance_scale: 引导系数
        :param prompt_enhancement: 是否启用提示词增强
        :param seeds: 种子值列表，每个图片对应一个种子值
        :param max_retries: 最大重试次数
        :return: API响应结果
        """
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # 准备请求参数
                data = {
                    "model": model,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "size": size,
                    "batch_size": batch_size,
                    "num_inference_steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "prompt_enhancement": prompt_enhancement
                }
                
                # 添加种子值
                if seeds and len(seeds) == batch_size:
                    data["seeds"] = seeds
                    self.logger.debug(f"使用种子值: {seeds}")
                else:
                    self.logger.warning("未提供种子值或种子值数量不匹配，将使用随机种子")
                
                # 发送请求
                self.logger.debug(f"发送请求到 {self.base_url}/images/generations")
                self.logger.debug(f"请求参数: {data}")
                
                response = self.session.post(
                    f"{self.base_url}/images/generations",
                    json=data,
                    timeout=300
                )
                
                # 检查响应状态
                if response.status_code == 200:
                    result = response.json()
                    
                    # 处理返回的种子值
                    if "data" in result:
                        images = result["data"]
                        if seeds and len(seeds) == len(images):
                            for i, img in enumerate(images):
                                if "seed" not in img:
                                    img["seed"] = seeds[i]
                        self.logger.debug(f"处理后的图片数据: {images}")
                    
                    return result
                    
                elif response.status_code == 429:
                    error_msg = "API请求超出限制，请稍后重试"
                    self.logger.warning(f"第{retry_count + 1}次尝试失败: {error_msg}")
                    if retry_count == max_retries - 1:
                        raise APIError(error_msg, code=429)
                    time.sleep(5 * (retry_count + 1))  # 指数退避
                
                elif response.status_code == 503:
                    error_msg = "API服务暂时不可用，请稍后重试"
                    self.logger.warning(f"第{retry_count + 1}次尝试失败: {error_msg}")
                    if retry_count == max_retries - 1:
                        raise APIError(error_msg, code=503)
                    time.sleep(5 * (retry_count + 1))
                
                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', response.text)
                    except:
                        error_msg = f"未知错误 (状态码: {response.status_code})"
                    
                    self.logger.error(f"API请求失败: {error_msg}")
                    if retry_count == max_retries - 1:
                        raise APIError(error_msg, code=response.status_code)
                
            except requests.exceptions.Timeout:
                error_msg = "请求超时，请检查网络状态"
                self.logger.warning(f"第{retry_count + 1}次尝试失败: {error_msg}")
                if retry_count == max_retries - 1:
                    raise APIError(error_msg, code=408)
                time.sleep(5 * (retry_count + 1))
                
            except requests.exceptions.ConnectionError:
                error_msg = "网络连接失败，请检查网络设置"
                self.logger.warning(f"第{retry_count + 1}次尝试失败: {error_msg}")
                if retry_count == max_retries - 1:
                    raise APIError(error_msg, code=503)
                time.sleep(5 * (retry_count + 1))
                
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"生成图片时出错: {last_error}")
                if retry_count == max_retries - 1:
                    if isinstance(e, APIError):
                        raise e
                    else:
                        raise APIError(f"生成图片失败: {last_error}", code=500)
                time.sleep(5 * (retry_count + 1))
            
            retry_count += 1
        
        raise APIError(f"达到最大重试次数，最后一次错误: {last_error}", code=500)
    
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
    
    def validate_params(self, params: Dict) -> None:
        if not params["prompt"].strip():
            raise ValueError("提示词不能为空")
        
        if not 0 <= params["guidance_scale"] <= 20:
            raise ValueError("引导系数必须在0-20之间")
        
        if "turbo" in params["model"].lower():
            params["num_inference_steps"] = 4
        elif not 1 <= params["num_inference_steps"] <= 50:
            raise ValueError("生成步数必须在1-50之间")
        
        if not params["random_seed"] and not 1 <= params["seed"] <= 9999999999:
            raise ValueError("随机种子必须在1-9999999999之间") 
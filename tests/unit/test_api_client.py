import pytest
from src.utils.api_client import SiliconFlowAPI, APIError
from pathlib import Path
import responses
import requests
import json

@pytest.fixture
def api_client():
    return SiliconFlowAPI("test_key")

@pytest.fixture
def mock_api_response():
    return {
        "data": [
            {
                "url": "http://example.com/image.png",
                "seed": 42
            }
        ],
        "timings": {"inference": 1.5}
    }

def test_api_client_init():
    # 测试基本初始化
    client = SiliconFlowAPI("test_key")
    assert client.api_key == "test_key"
    assert client.base_url == "https://api.siliconflow.cn/v1"
    
    # 测试代理设置
    proxy = {"http": "http://proxy:8080"}
    client_with_proxy = SiliconFlowAPI("test_key", proxy=proxy)
    assert client_with_proxy.session.proxies == proxy

@responses.activate
def test_generate_image_with_all_params(api_client, mock_api_response):
    responses.add(
        responses.POST,
        "https://api.siliconflow.cn/v1/images/generations",
        json=mock_api_response,
        status=200
    )
    
    result = api_client.generate_image(
        prompt="test prompt",
        model="stabilityai/stable-diffusion-3-5-large",
        negative_prompt="bad quality",
        size="1024x1024",
        batch_size=1,
        seeds=[42],
        num_inference_steps=20,
        guidance_scale=7.5,
        prompt_enhancement=True
    )
    
    assert result == mock_api_response
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == f"{api_client.base_url}/images/generations"
    
    request_body = json.loads(responses.calls[0].request.body.decode('utf-8'))
    assert request_body["prompt"] == "test prompt"
    assert request_body["model"] == "stabilityai/stable-diffusion-3-5-large"
    assert request_body["seeds"] == [42]

@responses.activate
def test_api_rate_limit_error(api_client):
    responses.add(
        responses.POST,
        "https://api.siliconflow.cn/v1/images/generations",
        json={"message": "Rate limit exceeded"},
        status=429
    )
    
    with pytest.raises(APIError) as exc_info:
        api_client.generate_image(
            prompt="test prompt",
            model="stabilityai/stable-diffusion-3-5-large"
        )
    assert exc_info.value.code == 429
    assert "API请求超出限制" in str(exc_info.value)

@responses.activate
def test_api_server_error(api_client):
    responses.add(
        responses.POST,
        "https://api.siliconflow.cn/v1/images/generations",
        json={"message": "Service unavailable"},
        status=503
    )
    
    with pytest.raises(APIError) as exc_info:
        api_client.generate_image(
            prompt="test prompt",
            model="stabilityai/stable-diffusion-3-5-large"
        )
    assert exc_info.value.code == 503
    assert "API服务暂时不可用" in str(exc_info.value)

@responses.activate
def test_validate_api_key(api_client):
    # 测试有效的API密钥
    responses.add(
        responses.GET,
        "https://api.siliconflow.cn/v1/models",
        json={"models": ["model1", "model2"]},
        status=200
    )
    assert api_client.validate_api_key() is True
    
    # 测试无效的API密钥
    responses.reset()
    responses.add(
        responses.GET,
        "https://api.siliconflow.cn/v1/models",
        json={"error": "Invalid API key"},
        status=401
    )
    assert api_client.validate_api_key() is False

def test_download_image_errors(api_client, tmp_path):
    test_image_path = tmp_path / "test.png"
    
    @responses.activate
    def test_network_error():
        responses.add(
            responses.GET,
            "http://example.com/image.png",
            body=requests.exceptions.ConnectionError()
        )
        
        with pytest.raises(APIError) as exc_info:
            api_client.download_image("http://example.com/image.png", test_image_path)
        assert "图片下载失败" in str(exc_info.value)
    
    test_network_error() 
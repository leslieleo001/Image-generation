# Silicon Flow 图片生成工具

[![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![PyQt Version](https://img.shields.io/badge/PyQt-6.6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

基于 Silicon Flow API 的 Windows 桌面图片生成工具，提供直观的界面和丰富的功能。

## 功能特点

- 🎨 单图生成
  - 详细的参数配置
  - 实时图片预览
  - 多种模型支持
  - 随机种子控制

- 📊 批量生成
  - Excel 导入导出
  - 批量任务管理
  - 进度监控
  - 错误处理

- ⚙️ 设置管理
  - API 密钥配置
  - 输出路径设置
  - 界面主题切换
  - 参数预设

## 快速开始

### 环境要求

- Windows 10 或更高版本
- Python 3.13 或更高版本
- Silicon Flow API 密钥

### 安装步骤

1. 克隆项目：
```bash
git clone <project-url>
cd project-name
```

2. 创建虚拟环境：
```bash
python -m venv venv
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 运行程序：
```bash
python -m src.main.main
```

## 使用指南

### 单图生成

1. 在设置中配置 API 密钥
2. 选择生成模型
3. 输入提示词
4. 调整参数
5. 点击生成
6. 预览并保存

### 批量生成

1. 准备 Excel 文件
2. 导入任务列表
3. 设置批量参数
4. 开始生成
5. 导出结果

## 项目结构

```
project/
├── docs/                # 文档目录
│   ├── PROJECT.md       # 项目说明
│   ├── REQUIREMENTS.md  # 需求文档
│   ├── DEVELOPMENT.md   # 开发文档
│   ├── TESTING.md       # 测试文档
│   ├── CHANGELOG.md     # 变更日志
│   └── FAQ.md           # 常见问题
├── src/                 # 源代码
│   ├── main/           # 主程序
│   ├── ui/             # 界面
│   └── utils/          # 工具
├── tests/              # 测试用例
├── config/             # 配置文件
├── output/             # 输出目录
├── presets/            # 预设目录
├── history/            # 历史记录
└── requirements.txt    # 依赖清单
```

## 开发相关

- [开发文档](docs/DEVELOPMENT.md)
- [需求文档](docs/REQUIREMENTS.md)
- [贡献指南](docs/CONTRIBUTING.md)
- [更新日志](docs/CHANGELOG.md)

## 测试

运行测试：
```bash
pytest -v
```

检查覆盖率：
```bash
pytest --cov=src
```

## 问题反馈

如果您发现任何问题或有建议，请：

1. 查看 [常见问题](docs/FAQ.md)
2. 提交 [Issue](issues)
3. 发送邮件至 [support@example.com](mailto:support@example.com)

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 致谢

- [Silicon Flow API](https://siliconflow.com) - 提供图片生成服务
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI 框架
- [pytest](https://docs.pytest.org/) - 测试框架 

## 运行方式

### 独立运行版本（推荐）
1. 下载最新版本的 `Silicon Flow.exe`
2. 创建一个新文件夹并将exe文件放入
3. 双击运行程序

### 源代码运行
1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 运行程序：`python src/main/main.py`

## 系统要求

### 独立运行版本
- Windows 10/11 64位系统
- 4GB以上内存
- 建议安装 Visual C++ Redistributable 2022

### 源代码运行
- Python 3.11 或更高版本
- 见 requirements.txt 中的依赖要求 
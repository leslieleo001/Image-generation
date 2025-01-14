# 需求文档

## 1. 功能需求

### 1.1 单图生成功能
- 模型选择
  * 支持多个模型：
    - stabilityai/stable-diffusion-3-5-large
    - stabilityai/stable-diffusion-3-medium
    - stabilityai/stable-diffusion-3-5-large-turbo
  * 自动调整参数范围
  * 显示模型特性说明

- 参数配置
  * 提示词和负面提示词输入
  * 生成步数 (1-50)
  * 引导系数 (0.1-20.0)
  * 提示增强开关
  * 随机种子控制 (1-2147483647)
  * 图片尺寸选择

- 预设管理
  * 保存当前参数为预设
  * 加载预设更新参数
  * 预设导入导出
  * 预设编辑和删除
  * 预设描述支持

- 历史记录
  * 自动记录生成历史
  * 显示时间戳和参数
  * 支持重新加载参数
  * 支持清空历史
  * 防止重复记录

- 图片预览
  * 鼠标滚轮缩放 (0.1-5.0倍)
  * 鼠标拖动查看
  * 适应窗口显示
  * 重置视图
  * 高性能渲染

### 1.2 批量生成功能
- Excel导入导出
  * 支持多种格式
  * 参数列映射
  * 错误检查

- 任务队列
  * 任务状态显示
  * 进度监控
  * 暂停/继续
  * 任务编辑
  * 优先级调整

- 错误处理
  * 自动重试
  * 错误日志
  * 批量错误处理
  * 状态恢复

### 1.3 设置功能
- API配置
  * API密钥管理
  * 连接测试
  * 错误提示

- 界面设置
  * 主题切换
  * 语言选择
  * 字体设置

- 路径配置
  * 输出目录
  * 临时文件
  * 预设存储

## 2. 非功能需求

### 2.1 性能要求
- 响应时间
  * 界面操作响应 < 100ms
  * 图片生成 < 30s
  * 批量处理 < 1min/张

- 资源使用
  * CPU使用率 < 50%
  * 内存占用 < 2GB
  * 磁盘空间 < 1GB

### 2.2 可用性要求
- 界面友好
  * 操作直观
  * 提示清晰
  * 错误友好

- 稳定性
  * 崩溃率 < 0.1%
  * 错误恢复机制
  * 数据保护

### 2.3 安全要求
- 数据安全
  * API密钥加密
  * 本地数据保护
  * 安全传输

- 访问控制
  * 用户认证
  * 操作日志
  * 权限管理

### 2.4 兼容性要求
- 系统支持
  * Windows 10+
  * macOS 10.15+
  * Linux主流发行版

- 分辨率适配
  * 最小 1920x1080
  * 推荐 2K/4K
  * DPI缩放

## 3. 技术要求

### 3.1 开发环境
- Python 3.13+
- PyQt6 6.6.0+
- Git版本控制

### 3.2 依赖要求
- requests：最新稳定版
- pandas：最新稳定版
- pillow：最新稳定版
- pytest：最新稳定版

### 3.3 代码规范
- PEP 8
- 类型注解
- 完整注释
- 单元测试

## 4. 验收标准

### 4.1 功能验收
- 单图生成：全部功能可用
- 批量生成：核心功能完成
- 设置功能：全部实现

### 4.2 性能验收
- 响应时间达标
- 资源使用合理
- 稳定性达标

### 4.3 测试覆盖
- 单元测试覆盖率 > 90%
- 集成测试通过
- 性能测试达标 

## 7. 单图生成功能需求

### 7.1 多图生成功能

#### 7.1.1 基本功能
- 必要功能：
  * 支持1-10张图片的批量生成
  * 生成过程显示进度
  * 生成完成后自动显示
  * 支持取消生成操作
- 可选功能：
  * 生成时间估算
  * 批量参数调整
  * 自定义生成数量范围

#### 7.1.2 图片预览功能
- 必要功能：
  * 缩略图列表显示
  * 点击预览大图
  * 支持图片缩放
  * 支持图片保存
- 可选功能：
  * 图片编辑
  * 图片比较
  * 批量导出
  * 拖拽排序

#### 7.1.3 历史记录功能
- 必要功能：
  * 独立的历史窗口
  * 表格形式显示记录
  * 支持记录预览
  * 支持记录导出
  * 支持清空历史
- 可选功能：
  * 记录搜索
  * 记录筛选
  * 记录分类
  * 记录标签

#### 7.1.4 多行文本输入
- 必要功能：
  * 支持多行输入
  * 自动换行
  * 滚动条
  * 复制粘贴
- 可选功能：
  * 语法高亮
  * 自动补全
  * 历史记录
  * 模板管理

### 7.2 性能需求

#### 7.2.1 响应时间
- 界面响应：<100ms
- 图片生成：
  * 单张：<30s
  * 多张：<60s
- 历史加载：<1s
- 缩略图显示：<500ms

#### 7.2.2 资源占用
- CPU使用率：<50%
- 内存占用：<500MB
- 磁盘空间：
  * 程序：<100MB
  * 历史记录：<1GB

### 7.3 可用性需求

#### 7.3.1 界面设计
- 布局要求：
  * 清晰的功能分区
  * 合理的空间利用
  * 统一的视觉风格
  * 响应式适配
- 交互要求：
  * 操作步骤简单
  * 反馈及时明确
  * 快捷键支持
  * 错误提示友好

#### 7.3.2 用户体验
- 易用性：
  * 功能容易理解
  * 操作简单直观
  * 帮助信息完整
  * 学习成本低
- 可访问性：
  * 支持键盘操作
  * 支持屏幕阅读
  * 支持主题切换
  * 支持字体缩放

### 7.4 安全性需求

#### 7.4.1 数据安全
- API密钥保护：
  * 加密存储
  * 访问控制
  * 定期更新
  * 泄露提醒
- 图片安全：
  * 安全存储
  * 访问权限
  * 删除确认
  * 备份恢复

#### 7.4.2 操作安全
- 权限控制：
  * 功能访问控制
  * 操作日志记录
  * 异常操作提醒
  * 敏感操作确认
- 异常处理：
  * 输入验证
  * 错误恢复
  * 状态保持
  * 数据一致性 

## 批量生成功能需求

### 功能需求

1. 提示词管理
   - 必须支持多行文本输入，每行作为一个独立的提示词
   - 必须支持从TXT和Excel文件导入提示词列表
   - 必须支持负面提示词设置，应用于所有生成任务
   - 应该提供提示词预览和编辑功能

2. 参数设置
   - 必须支持选择生成模型
   - 必须支持设置图片尺寸
   - 必须支持调整生成步数（turbo模型除外）
   - 必须支持调整引导系数
   - 必须支持设置随机种子
   - 应该支持提示词增强功能
   - 应该支持参数预设保存和加载

3. 生成控制
   - 必须显示整体生成进度
   - 必须显示当前处理的提示词信息
   - 必须支持生成过程中取消操作
   - 应该支持暂停和继续功能
   - 应该支持失败重试功能

4. 历史记录
   - 必须记录每次生成的参数和结果
   - 必须支持显示生成图片的缩略图
   - 必须支持从历史记录还原参数
   - 必须支持清空历史记录
   - 应该支持历史记录搜索和筛选
   - 应该支持历史记录导出功能

### 性能需求

1. 响应时间
   - 界面操作响应时间不超过100ms
   - 提示词导入处理时间不超过5秒（1000条数据以内）
   - 历史记录加载时间不超过3秒

2. 并发处理
   - 生成过程不得影响界面响应
   - 支持同时处理多个提示词
   - 失败任务不影响其他任务继续执行

3. 资源占用
   - 内存占用不超过500MB
   - CPU占用率峰值不超过50%
   - 磁盘写入速度不超过10MB/s

### 可用性需求

1. 界面设计
   - 必须提供清晰的操作指引
   - 必须显示当前处理状态
   - 必须提供错误提示和处理建议
   - 应该支持界面主题切换
   - 应该支持界面布局调整

2. 操作便利性
   - 必须支持键盘快捷键操作
   - 必须支持拖拽文件导入
   - 必须支持参数快速复制
   - 应该支持常用参数预设
   - 应该支持批处理操作

3. 错误处理
   - 必须提供详细的错误信息
   - 必须支持错误日志记录
   - 必须支持失败任务重试
   - 应该提供问题诊断工具
   - 应该支持自动错误报告

### 安全需求

1. 数据安全
   - 必须安全存储API密钥
   - 必须加密保存敏感信息
   - 必须定期清理临时文件
   - 应该支持数据备份功能

2. 访问控制
   - 必须验证API调用权限
   - 必须限制敏感操作权限
   - 应该支持操作日志记录
   - 应该支持多用户隔离

### 兼容性需求

1. 系统兼容
   - 必须支持Windows 10及以上版本
   - 必须支持macOS 10.15及以上版本
   - 应该支持主流Linux发行版

2. 文件格式
   - 必须支持TXT文本导入
   - 必须支持Excel文件导入
   - 必须支持PNG图片保存
   - 应该支持其他常用图片格式 
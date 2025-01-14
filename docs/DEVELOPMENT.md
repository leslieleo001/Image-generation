# 开发文档

## 1. 开发环境

### 1.1 环境要求
- 操作系统：Windows 10/11
- Python：3.13+
- PyQt6：>= 6.6.0
- requests：>= 2.31.0
- pandas：>= 2.2.0
- pillow：>= 10.2.0

### 1.2 环境配置
1. 克隆项目
```bash
git clone https://github.com/your-username/silicon-flow-generator.git
cd silicon-flow-generator
```

2. 创建虚拟环境
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

## 2. 项目结构

```
project/
├── docs/                # 文档目录
│   ├── PROJECT.md       # 项目说明
│   ├── REQUIREMENTS.md  # 需求文档
│   ├── DEVELOPMENT.md   # 开发文档
│   ├── CHANGELOG.md     # 变更日志
│   ├── CONTRIBUTING.md  # 贡献指南
│   └── FAQ.md          # 常见问题
├── src/                 # 源代码
│   ├── main/           # 主程序
│   │   └── main.py     # 程序入口
│   ├── ui/             # 界面模块
│   │   ├── main_window.py    # 主窗口
│   │   ├── single_gen.py     # 单图生成
│   │   ├── batch_gen.py      # 批量生成
│   │   ├── image_preview.py  # 图片预览
│   │   └── settings.py       # 设置界面
│   └── utils/          # 工具模块
│       ├── api_client.py     # API客户端
│       ├── config_manager.py # 配置管理
│       ├── preset_manager.py # 预设管理
│       ├── excel_handler.py  # Excel处理
│       └── task_queue.py     # 任务队列
├── tests/              # 测试用例
│   └── unit/          # 单元测试
├── requirements.txt    # 依赖清单
└── README.md          # 项目说明
```

## 3. 开发规范

### 3.1 代码规范
- 遵循PEP 8规范
- 使用类型注解
- 编写详细注释
- 保持代码简洁清晰

### 3.2 测试规范
- 编写单元测试
- 测试覆盖率 > 80%
- 使用pytest框架
- 模拟外部依赖

### 3.3 Git提交规范
- feat: 新功能
- fix: 修复问题
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试相关
- chore: 其他修改

## 4. 测试结果

### 4.1 单图生成功能
- ✅ API管理器测试通过
- ✅ 界面初始化测试通过
- ✅ 模型切换测试通过
- ✅ 随机种子设置测试通过
- ✅ 参数获取测试通过
- ✅ 图片生成验证测试通过
- ✅ 预设管理相关测试通过

### 4.2 图片预览功能
- ✅ 初始化测试通过
- ✅ 图片设置测试通过
- ✅ 滚轮缩放测试通过
- ✅ 鼠标拖动测试通过
- ✅ 适应窗口测试通过
- ✅ 重置视图测试通过
- ✅ 缩放限制测试通过
- ✅ 拖动限制测试通过

### 4.3 批量生成功能
- ✅ 初始化测试通过
- ✅ Excel导入导出测试通过
- ✅ 任务列表操作测试通过
- ✅ 任务编辑测试通过
- ✅ 任务排序测试通过
- ✅ 错误处理测试通过

### 4.4 其他功能
- ✅ 配置管理器测试通过
- ✅ Excel处理器测试通过
- ✅ 预设管理器测试通过
- ✅ 设置界面测试通过

## 5. 已知问题

### 5.1 高优先级
- [ ] Qt配置选项警告需要处理
- [ ] 图片预览组件的空QPixmap警告需要优化

### 5.2 中优先级
- [ ] 批量生成功能的性能需要优化
- [ ] 批量生成的测试覆盖率需要提高

### 5.3 低优先级
- [ ] 文档还需要进一步完善
- [ ] 用户使用指南需要补充

## 6. 下一步计划
1. 处理Qt配置选项警告
2. 优化图片预览组件
3. 提高批量生成功能的测试覆盖率
4. 优化批量生成的性能
5. 完善项目文档
6. 准备v0.2.3版本发布

## 7. 功能实现

### 7.1 单图生成功能

#### 7.1.1 基本功能
- 界面布局：使用QVBoxLayout和QFormLayout
- 参数配置：使用QComboBox和QSpinBox等
- 图片预览：使用QLabel显示QPixmap
- 异步生成：使用QThread避免界面阻塞

#### 7.1.2 多图生成功能
- 主要类：`ImageGenerationThread`
- 核心功能：
  * 支持批量生成（1-10张）
  * 异步下载和处理
  * 缩略图管理
  * 图片预览
- 实现细节：
  ```python
  class ImageGenerationThread(QThread):
      finished = pyqtSignal(list)  # 发送图片列表
      error = pyqtSignal(str)
      
      def run(self):
          # 调用API生成图片
          result = api.generate_image(**self.params)
          
          # 下载所有图片
          image_data_list = []
          for image_info in result["images"]:
              response = requests.get(image_info["url"])
              image_data_list.append(response.content)
              
          self.finished.emit(image_data_list)
  ```

#### 7.1.3 缩略图管理
- 主要组件：`QListWidget`
- 功能实现：
  * 图标模式显示
  * 固定大小缩略图
  * 右键菜单支持
  * 点击预览
- 代码示例：
  ```python
  def init_thumbnail_list(self):
      self.thumbnails_list.setViewMode(QListWidget.ViewMode.IconMode)
      self.thumbnails_list.setIconSize(QSize(80, 80))
      self.thumbnails_list.setSpacing(10)
      self.thumbnails_list.setResizeMode(QListWidget.ResizeMode.Adjust)
      
  def add_thumbnail(self, image_data):
      pixmap = QPixmap()
      pixmap.loadFromData(image_data)
      scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio)
      
      item = QListWidgetItem()
      item.setIcon(QIcon(scaled_pixmap))
      item.setData(Qt.UserRole, image_data)
      self.thumbnails_list.addItem(item)
  ```

#### 7.1.4 历史记录管理
- 主要类：`HistoryWindow`
- 核心功能：
  * 表格形式显示
  * 预览和加载
  * Excel导出（含图片）
  * 批量操作
  * 多图片支持
- 数据结构：
  ```python
  {
      "timestamp": "2024-01-13T20:00:00",
      "params": {
          "prompt": "提示词",
          "negative_prompt": "负面提示词",
          "model": "模型名称",
          "size": "图片尺寸",
          "num_inference_steps": 20,
          "guidance_scale": 7.5,
          "prompt_enhancement": false,
          "batch_size": 1,
          "seed": "随机"
      },
      "image_path": "保存路径"
  }
  ```
- Excel导出功能：
  ```python
  def export_history(self):
      # 创建Excel工作簿
      wb = Workbook()
      ws = wb.active
      
      # 设置表头
      headers = ["时间", "预览图", "提示词", "负面提示词", "模型", "图片尺寸", 
                "生成步数", "引导系数", "提示增强", "随机种子", "图片路径"]
      
      # 写入数据和图片
      for record in records:
          # 写入文本数据
          ws.cell(row=row, column=1, value=record["timestamp"])
          ws.cell(row=row, column=3, value=record["params"]["prompt"])
          # ... 其他数据 ...
          
          # 插入图片预览
          if Path(record["image_path"]).exists():
              img = Image(record["image_path"])
              img.width = target_width
              img.height = target_height
              ws.add_image(img, f"B{row}")
  ```
- 信号机制：
  ```python
  class HistoryManager(QObject):
      history_changed = pyqtSignal()  # 历史记录变化信号
      
      def add_record(self, params, image_path):
          self.history.insert(0, {
              "timestamp": datetime.now().isoformat(),
              "params": params,
              "image_path": str(image_path)
          })
          self.save_history()
          self.history_changed.emit()
  ```

#### 7.1.5 多行文本输入
- 组件：`QTextEdit`
- 功能特点：
  * 支持换行
  * 自动调整大小
  * 滚动条支持
  * 复制粘贴
- 实现示例：
  ```python
  def init_text_inputs(self):
      self.prompt_input = QTextEdit()
      self.prompt_input.setMinimumHeight(80)
      self.prompt_input.setStyleSheet("QTextEdit { padding: 5px; }")
      
      self.negative_prompt = QTextEdit()
      self.negative_prompt.setMinimumHeight(80)
      self.negative_prompt.setStyleSheet("QTextEdit { padding: 5px; }")
  ```

### 7.2 批量生成功能

#### 7.2.1 Excel处理
- 主要类：`ExcelHandler`
- 功能：
  - 读取任务列表
  - 导出结果
  - 创建模板
- 数据格式：
  - 必需列：提示词、模型、尺寸
  - 可选列：状态、结果路径
- 错误处理：
  - 文件不存在
  - 格式错误
  - 必需列缺失
  - 导出失败

#### 7.2.2 任务队列
- 主要类：`TaskQueue`
- 核心功能：
  - 任务添加和清空
  - 启动/暂停/恢复/停止控制
  - 任务状态管理
  - 进度跟踪
- 线程安全：
  - 使用 Lock 保护共享资源
  - Event 控制线程状态
  - 安全的任务状态更新
- 回调机制：
  - 任务完成回调
  - 任务错误回调
  - 进度更新回调
- 错误处理：
  - API调用错误
  - 线程异常
  - 资源清理
  - 状态恢复

#### 7.2.3 界面实现
- 主要类：`BatchGenTab`
- 界面组件：
  - 任务表格
  - 进度条
  - 控制按钮
  - 排序功能
- 功能实现：
  - Excel导入导出
  - 任务编辑
  - 状态显示
  - 结果查看
- 交互优化：
  - 按钮状态管理
  - 实时进度更新
  - 错误提示
  - 操作确认

#### 7.2.4 测试策略
- 单元测试：
  - Excel处理测试
  - 任务队列测试
  - UI组件测试
- 集成测试：
  - 导入导出流程
  - 任务处理流程
  - 界面交互流程
- 性能测试：
  - 大量任务处理
  - 内存使用
  - 响应时间
- 错误测试：
  - 异常处理
  - 边界条件
  - 资源清理

### 7.3 API集成

#### 7.3.1 API客户端
- 主要类：`SiliconFlowAPI`
- 核心功能：
  - API密钥验证
  - 图片生成请求
  - 图片下载
  - 错误处理
- 请求格式：
  ```python
  {
      "prompt": "提示词",
      "negative_prompt": "负面提示词",
      "model": "模型名称",
      "size": "图片尺寸",
      "batch_size": "批次大小",
      "num_inference_steps": "生成步数",
      "guidance_scale": "引导系数",
      "prompt_enhancement": "提示增强",
      "seed": "随机种子"  # 可选
  }
  ```
- 错误处理：
  - 401: API密钥无效
  - 429: 请求限制
  - 503: 服务过载
  - 网络错误
  - 下载失败

#### 7.3.2 API管理器
- 主要类：`APIManager`
- 核心功能：
  - API实例管理
  - 动态更新API密钥
  - 生命周期管理
- 实现细节：
  ```python
  class APIManager:
      def __init__(self, config: ConfigManager):
          self._config = config
          self._api = None
          
      def refresh_api(self) -> SiliconFlowAPI:
          api_key = self._config.get("api.key")
          if not api_key:
              return None
          self._api = SiliconFlowAPI(api_key)
          return self._api
          
      @property
      def api(self) -> SiliconFlowAPI:
          return self._api
  ```
- 使用方式：
  - 单例模式
  - 配置驱动
  - 懒加载
  - 线程安全

#### 7.3.3 异步处理
- 主要类：`ImageGenerationThread`
- 核心功能：
  - 异步图片生成
  - 进度跟踪
  - 错误处理
- 信号定义：
  ```python
  class ImageGenerationThread(QThread):
      finished = pyqtSignal(bytes)  # 生成完成信号
      error = pyqtSignal(str)      # 错误信号
      progress = pyqtSignal(int)   # 进度信号
  ```
- 实现细节：
  - 使用QThread
  - 信号槽机制
  - 异常捕获
  - 资源清理

#### 7.3.4 参数验证
- 验证规则：
  - prompt: 不能为空
  - guidance_scale: 0-20
  - num_inference_steps: 
    - turbo模型固定为4
    - 其他模型1-50
  - seed: 1-2147483647
- 实现方式：
  ```python
  def validate_params(self, params: Dict) -> None:
      if not params["prompt"].strip():
          raise ValueError("提示词不能为空")
          
      if not 0 <= params["guidance_scale"] <= 20:
          raise ValueError("引导系数必须在0-20之间")
          
      if "turbo" in params["model"].lower():
          params["num_inference_steps"] = 4
      elif not 1 <= params["num_inference_steps"] <= 50:
          raise ValueError("生成步数必须在1-50之间")
          
      if not params["random_seed"] and not 1 <= params["seed"] <= 2147483647:
          raise ValueError("随机种子必须在1-2147483647之间")
  ```

#### 7.3.5 错误处理
- 错误类型：
  ```python
  class APIError(Exception):
      def __init__(self, message: str, status_code: int = None):
          self.message = message
          self.status_code = status_code
  ```
- 处理策略：
  - API密钥验证失败：提示重新输入
  - 请求限制：建议稍后重试
  - 服务过载：提示服务繁忙
  - 网络错误：检查网络连接
  - 参数错误：显示具体错误信息
- 用户反馈：
  - 错误提示对话框
  - 状态栏消息
  - 日志记录

## 8. 测试说明

### 8.1 单元测试
- API测试
- 配置测试
- UI组件测试
- 历史记录测试：
  - test_history_manager_init
  - test_history_manager_add_record
  - test_history_manager_clear
  - test_single_gen_history_integration
  - test_history_load_error_handling
  - test_history_save_error_handling

### 8.2 集成测试
- 功能集成测试
- 界面集成测试
- 数据流测试

## 9. 部署说明

### 9.1 打包
- 使用PyInstaller
- 配置文件处理
- 资源文件打包
- 依赖处理

### 9.2 安装
- 环境检查
- 配置初始化
- 权限设置
- 快捷方式创建

## 10. 维护说明

### 10.1 日志管理
- 运行日志
- 错误日志
- 历史记录
- 性能监控

### 10.2 配置管理
- 配置文件位置
- 配置项说明
- 默认配置
- 用户配置

### 10.3 错误处理
- 异常捕获
- 错误提示
- 恢复机制
- 日志记录

## 11. 性能优化

### 11.1 优化方向
- 减少API调用
- 优化内存使用
- 提高并发效率
- 优化UI响应

### 11.2 优化方法
- 使用缓存
- 延迟加载
- 批量处理
- 资源复用

## 12. 安全说明

### 12.1 数据安全
- API密钥保护
- 历史记录加密
- 配置文件安全
- 错误日志脱敏

### 12.2 访问控制
- 文件权限
- 配置权限
- 功能权限
- 数据权限 

## 任务队列实现

### 概述
任务队列用于管理批量图片生成任务，提供了线程安全的任务处理机制。主要功能包括：
- 任务添加和清理
- 任务状态管理
- 线程控制（启动、暂停、恢复、停止）
- 进度回调
- 错误处理

### 核心类
```python
class TaskQueue:
    def __init__(self, api: SiliconFlowAPI):
        # 初始化队列和状态
        self.queue = Queue()
        self.tasks: List[GenerationTask] = []
        self._current_task: Optional[GenerationTask] = None
        self._current_task_lock = Lock()
        self.worker_thread: Optional[Thread] = None
        self.pause_event = Event()
        self.stop_event = Event()
        self.task_lock = Lock()
```

### 线程安全机制
1. 属性访问保护
   - 使用 `Lock` 保护当前任务访问
   - 使用 property 装饰器实现安全访问
   - 任务列表操作使用锁保护

2. 事件同步
   - 使用 `Event` 控制暂停/恢复
   - 使用 `Event` 控制停止
   - 超时机制避免永久等待

3. 资源清理
   - 线程终止时清理资源
   - 任务状态正确更新
   - 回调函数异常处理

### 错误处理
1. API调用错误
   - 捕获并记录异常
   - 更新任务状态
   - 通知错误回调

2. 回调函数错误
   - 异常隔离
   - 日志记录
   - 不影响主流程

3. 线程异常
   - 安全停止机制
   - 资源正确释放
   - 状态一致性保证

### 测试策略
1. 单元测试
   - 基本功能测试
   - 线程控制测试
   - 错误处理测试

2. 集成测试
   - API交互测试
   - 回调机制测试
   - 资源清理测试

### 使用示例
```python
# 创建任务队列
queue = TaskQueue(api_client)

# 设置回调
queue.on_progress = lambda current, total: print(f"进度: {current}/{total}")
queue.on_task_complete = lambda task: print(f"任务完成: {task.prompt}")
queue.on_task_error = lambda task, error: print(f"任务失败: {error}")

# 添加任务
tasks = [GenerationTask(...), GenerationTask(...)]
queue.add_tasks(tasks)

# 启动处理
queue.start()

# 暂停/恢复
queue.pause()
queue.resume()

# 停止并清理
queue.stop()
queue.clear_tasks()
``` 

## 图片预览组件

### 组件概述
`ImagePreviewWidget` 是一个基于 `QLabel` 的自定义组件，提供图片预览、缩放和拖动功能。主要用于显示生成的图片，支持用户交互查看图片细节。

### 核心功能
1. 图片显示
   - 继承自 `QLabel`，支持显示 `QPixmap` 格式图片
   - 居中显示图片，保持宽高比
   - 支持边框显示和自定义样式

2. 缩放功能
   - 使用鼠标滚轮进行缩放
   - 缩放范围：0.1-5.0 倍
   - 缩放时保持鼠标位置不变
   - 使用平滑转换算法确保图片质量

3. 拖动功能
   - 支持鼠标左键拖动
   - 实时边界检查，防止拖出视图
   - 拖动时显示抓手光标
   - 优化拖动性能，减少重绘

4. 视图控制
   - 支持重置视图（恢复原始大小和位置）
   - 支持适应窗口大小（自动计算最佳缩放比例）
   - 处理窗口大小改变事件

### 实现细节
1. 状态管理
   ```python
   self._pixmap = None          # 原始图片
   self._scaled_pixmap = None   # 缩放后的图片
   self._scale = 1.0            # 当前缩放比例
   self._dragging = False       # 是否正在拖动
   self._scroll_offset = QPoint() # 滚动偏移量
   ```

2. 缩放实现
   ```python
   def wheelEvent(self, event):
       # 计算新的缩放比例
       delta = event.angleDelta().y()
       scale_delta = 0.1 if delta > 0 else -0.1
       new_scale = max(self._min_scale, min(self._max_scale, self._scale + scale_delta))
       
       # 更新缩放
       if new_scale != self._scale:
           self._scale = new_scale
           self._update_scaled_pixmap()
   ```

3. 拖动实现
   ```python
   def mouseMoveEvent(self, event):
       if self._dragging:
           # 计算新的偏移
           delta = event.pos() - self._drag_start
           new_offset = self._scroll_offset + delta
           
           # 应用边界限制
           max_x = max(0, (self._scaled_pixmap.width() - self.width()) // 2)
           new_offset.setX(max(-max_x, min(max_x, new_offset.x())))
   ```

### 测试策略
1. 单元测试
   - 测试初始化状态
   - 测试图片设置
   - 测试缩放功能（包括边界条件）
   - 测试拖动功能（包括边界检查）
   - 测试视图控制功能

2. 集成测试
   - 测试与主界面的集成
   - 测试与图片生成功能的配合
   - 测试内存使用情况

3. 性能测试
   - 测试大图片的加载和缩放性能
   - 测试拖动的流畅度
   - 测试内存占用

### 使用示例
```python
# 创建预览组件
preview = ImagePreviewWidget()
preview.setMinimumSize(100, 100)

# 设置图片
pixmap = QPixmap("image.png")
preview.setPixmap(pixmap)

# 适应窗口大小
preview.fit_to_view()

# 重置视图
preview.reset_view()
```

### 注意事项
1. 性能优化
   - 使用 `QPixmap.scaled()` 时选择合适的转换模式
   - 避免频繁重绘，使用 `update()` 而不是 `repaint()`
   - 缓存缩放后的图片，避免重复计算

2. 内存管理
   - 及时释放不需要的图片资源
   - 控制缩放范围，防止内存占用过大
   - 使用 `Qt.TransformationMode.SmoothTransformation` 时注意性能开销

3. 用户体验
   - 提供合适的鼠标光标反馈
   - 确保拖动和缩放的平滑性
   - 保持界面响应及时
``` 

## 批量生成功能

### 功能概述
批量生成功能允许用户同时处理多个提示词，自动生成多张图片。主要包含以下功能：

1. 提示词管理
   - 支持多行文本输入，每行一个提示词
   - 支持从TXT和Excel文件导入提示词
   - 支持负面提示词设置

2. 参数设置
   - 模型选择（支持3种模型）
   - 图片尺寸选择
   - 生成步数设置（turbo模型固定为4步）
   - 引导系数调整
   - 随机种子控制
   - 提示词增强开关

3. 生成控制
   - 显示生成进度条
   - 实时状态提示
   - 支持取消生成
   - 自动保存生成的图片

4. 历史记录
   - 显示生成历史，包含缩略图
   - 支持参数还原
   - 支持清空历史

### 实现细节

#### 1. 批量生成线程
```python
class BatchGenerationThread(QThread):
    progress = pyqtSignal(str)  # 进度信号
    error = pyqtSignal(str)     # 错误信号
    success = pyqtSignal(list)  # 成功信号
```

- 使用QThread处理生成任务，避免界面卡顿
- 通过信号机制与主界面通信
- 支持进度更新、错误处理和成功回调

#### 2. 参数处理
```python
params = {
    "negative_prompt": negative,
    "model": model,
    "image_size": size,
    "num_inference_steps": steps,
    "guidance_scale": guidance,
    "seed": seed,
    "enhance_prompt": enhance
}
```

- 统一参数格式，确保与API要求一致
- 支持默认值设置和参数验证

#### 3. 文件命名规则
支持以下变量：
- {timestamp}: 时间戳
- {date}: 日期
- {time}: 时间
- {prompt}: 提示词（前20字符）
- {model}: 模型名称
- {seed}: 种子值
- {index}: 序号
- {size}: 图片尺寸

#### 4. 历史记录格式
```python
history_item = {
    "timestamp": "ISO格式时间戳",
    "params": {
        "prompt": "提示词",
        "negative_prompt": "负面提示词",
        "model": "模型名称",
        "image_size": "图片尺寸",
        "num_inference_steps": "步数",
        "guidance_scale": "引导系数",
        "seed": "种子值",
        "prompt_enhancement": "是否启用提示增强",
        "batch_size": 1
    },
    "image_paths": ["图片路径列表"]
}
```

### 使用说明

1. 输入提示词
   - 直接在文本框中输入，每行一个提示词
   - 或点击"导入提示词"按钮从文件导入

2. 设置参数
   - 选择合适的模型和参数
   - 对于turbo模型，步数将固定为4

3. 开始生成
   - 点击"批量生成"按钮开始处理
   - 可以通过进度条查看进度
   - 生成完成后会显示提示信息

4. 查看历史
   - 在右侧面板查看生成历史
   - 双击历史记录可以还原参数
   - 点击"清空历史"可以清除所有记录

### 注意事项

1. 性能考虑
   - 批量生成时注意控制提示词数量
   - 建议每批不超过20个提示词
   - 生成过程中避免重复点击生成按钮

2. 错误处理
   - 每个提示词独立处理，单个失败不影响其他
   - 错误信息会实时显示
   - 最终会统计成功生成的数量

3. 文件管理
   - 图片自动保存到配置的输出目录
   - 文件名根据命名规则自动生成
   - 确保输出目录有足够空间
``` 
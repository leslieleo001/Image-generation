## 7. 单图生成测试

### 7.1 多图生成功能测试

#### 7.1.1 基本功能测试
- 测试项：
  * 图片数量选择（1-10张）
  * 生成按钮响应
  * 进度显示
  * 错误处理
- 测试用例：
  ```python
  def test_multi_image_generation():
      # 初始化
      tab = SingleGenTab()
      
      # 测试数量选择
      assert tab.num_images_spin.minimum() == 1
      assert tab.num_images_spin.maximum() == 10
      
      # 测试生成按钮状态
      assert tab.generate_btn.isEnabled()
      
      # 测试生成过程
      tab.num_images_spin.setValue(3)
      tab.generate_btn.click()
      
      # 验证结果
      assert len(tab.current_images) == 3
  ```

#### 7.1.2 缩略图功能测试
- 测试项：
  * 缩略图添加
  * 缩略图点击
  * 右键菜单
  * 图片预览
- 测试用例：
  ```python
  def test_thumbnail_functionality():
      # 初始化
      tab = SingleGenTab()
      
      # 测试添加缩略图
      image_data = b"测试图片数据"
      tab.add_thumbnail(image_data)
      assert tab.thumbnails_list.count() == 1
      
      # 测试点击预览
      item = tab.thumbnails_list.item(0)
      tab.on_thumbnail_clicked(item)
      assert tab.preview_label.pixmap() is not None
  ```

#### 7.1.3 历史记录测试
- 测试项：
  * 记录添加
  * 记录加载
  * 记录导出
  * 记录清空
- 测试用例：
  ```python
  def test_history_functionality():
      # 初始化
      history = HistoryManager()
      
      # 测试添加记录
      params = {
          "prompt": "测试提示词",
          "model": "test_model",
          "size": "512x512"
      }
      history.add_record(params, "test.png")
      assert len(history.get_records()) == 1
      
      # 测试清空记录
      history.clear_history()
      assert len(history.get_records()) == 0
  ```

#### 7.1.4 多行文本输入测试
- 测试项：
  * 文本输入
  * 换行处理
  * 滚动条
  * 复制粘贴
- 测试用例：
  ```python
  def test_text_input_functionality():
      # 初始化
      tab = SingleGenTab()
      
      # 测试多行输入
      test_text = "第一行\n第二行\n第三行"
      tab.prompt_input.setPlainText(test_text)
      assert tab.prompt_input.toPlainText() == test_text
      
      # 测试最小高度
      assert tab.prompt_input.minimumHeight() == 80
  ```

### 7.2 错误处理测试

#### 7.2.1 API错误测试
- 测试项：
  * API密钥无效
  * 网络连接失败
  * 服务器错误
  * 超时处理
- 测试用例：
  ```python
  def test_api_error_handling():
      # 初始化
      tab = SingleGenTab()
      
      # 测试无效API密钥
      tab.api_manager.api_key = "invalid_key"
      tab.generate_btn.click()
      # 验证错误提示
      
      # 测试网络错误
      with patch("requests.post") as mock_post:
          mock_post.side_effect = ConnectionError()
          tab.generate_btn.click()
          # 验证错误提示
  ```

#### 7.2.2 参数验证测试
- 测试项：
  * 必填参数检查
  * 参数范围验证
  * 特殊字符处理
- 测试用例：
  ```python
  def test_parameter_validation():
      # 初始化
      tab = SingleGenTab()
      
      # 测试空提示词
      tab.prompt_input.setPlainText("")
      tab.generate_btn.click()
      # 验证错误提示
      
      # 测试参数范围
      tab.num_images_spin.setValue(11)
      assert tab.num_images_spin.value() == 10
  ```

## 批量生成功能测试

### 1. 提示词管理测试

#### 1.1 文本输入测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 多行输入 | 1. 在提示词输入框中输入多行文本<br>2. 每行输入不同的提示词 | 每行文本被正确识别为独立的提示词 |
| 空行处理 | 1. 输入包含空行的文本<br>2. 点击生成按钮 | 空行被自动忽略，不影响生成过程 |
| 特殊字符 | 1. 输入包含特殊字符的提示词<br>2. 检查处理结果 | 特殊字符被正确处理，不影响生成 |

#### 1.2 文件导入测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| TXT导入 | 1. 点击导入按钮<br>2. 选择TXT文件<br>3. 确认导入 | 文件内容被正确导入到提示词输入框 |
| Excel导入 | 1. 点击导入按钮<br>2. 选择Excel文件<br>3. 确认导入 | 第一列数据被正确导入为提示词 |
| 编码兼容 | 1. 导入不同编码的文本文件<br>2. 检查显示结果 | 正确显示各种编码的文本内容 |

### 2. 参数设置测试

#### 2.1 模型选择测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 模型切换 | 1. 依次选择不同模型<br>2. 观察参数变化 | 参数随模型自动调整 |
| Turbo模型 | 1. 选择turbo模型<br>2. 检查步数设置 | 步数自动设为4且不可修改 |

#### 2.2 参数验证测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 步数范围 | 1. 输入不同的步数值<br>2. 测试边界值 | 只允许1-50的整数值 |
| 引导系数 | 1. 调整引导系数<br>2. 测试边界值 | 只允许0-20的浮点数 |
| 随机种子 | 1. 设置-1作为种子值<br>2. 设置具体数值 | -1生成随机种子，具体值固定结果 |

### 3. 生成控制测试

#### 3.1 进度显示测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 进度条 | 1. 启动批量生成<br>2. 观察进度条变化 | 进度条准确反映当前进度 |
| 状态提示 | 1. 观察生成过程<br>2. 检查状态文本 | 显示当前处理的提示词信息 |

#### 3.2 错误处理测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| API错误 | 1. 模拟API调用失败<br>2. 观察错误处理 | 显示错误信息，继续处理其他任务 |
| 网络中断 | 1. 断开网络连接<br>2. 观察程序行为 | 显示网络错误，支持重试 |

### 4. 历史记录测试

#### 4.1 记录保存测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 参数记录 | 1. 生成图片<br>2. 检查历史记录 | 完整保存所有生成参数 |
| 图片链接 | 1. 查看历史记录<br>2. 打开保存的图片 | 正确保存和显示图片路径 |

#### 4.2 历史操作测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 参数还原 | 1. 双击历史记录<br>2. 检查参数设置 | 准确还原历史参数设置 |
| 清空记录 | 1. 点击清空按钮<br>2. 确认操作 | 正确清空所有历史记录 |

### 5. 性能测试

#### 5.1 响应性能测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 界面响应 | 1. 生成过程中操作界面<br>2. 测试各个控件 | 界面保持响应，不出现卡顿 |
| 大量数据 | 1. 导入1000条提示词<br>2. 观察处理性能 | 在5秒内完成导入处理 |

#### 5.2 资源占用测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 内存使用 | 1. 监控内存占用<br>2. 执行批量生成 | 内存占用不超过500MB |
| CPU负载 | 1. 监控CPU使用率<br>2. 执行批量生成 | CPU峰值不超过50% |

### 6. 兼容性测试

#### 6.1 系统兼容测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| Windows | 1. 在Windows系统运行<br>2. 测试所有功能 | 功能正常，界面正确显示 |
| macOS | 1. 在macOS系统运行<br>2. 测试所有功能 | 功能正常，界面正确显示 |

#### 6.2 文件兼容测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 文本格式 | 1. 测试不同格式文本文件<br>2. 检查导入结果 | 正确处理各种文本格式 |
| Excel版本 | 1. 测试不同版本Excel文件<br>2. 检查导入结果 | 兼容主流Excel版本 | 
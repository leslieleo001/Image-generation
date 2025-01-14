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

#### 3.1 取消功能测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 取消响应 | 1. 开始批量生成<br>2. 点击取消按钮<br>3. 确认取消 | 生成立即停止，UI保持响应 |
| 重复取消 | 1. 点击取消按钮<br>2. 再次点击取消按钮 | 第二次点击被忽略 |
| 按钮状态 | 1. 点击取消按钮<br>2. 确认取消 | 所有按钮被禁用，直到取消完成 |
| 进度显示 | 1. 取消生成<br>2. 观察进度文本 | 显示"正在取消生成..."和最终结果 |

#### 3.2 历史记录测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 记录创建 | 1. 生成多张图片<br>2. 检查历史记录 | 每张图片有独立的历史记录 |
| 记录时机 | 1. 观察生成过程<br>2. 检查历史记录更新 | 图片保存后立即创建记录 |
| 取消处理 | 1. 生成过程中取消<br>2. 检查历史记录 | 已生成图片的记录被保留 |

#### 3.3 性能测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 取消性能 | 1. 生成大量图片时取消<br>2. 观察UI响应 | UI保持流畅，无卡顿 |
| 内存使用 | 1. 监控内存占用<br>2. 执行取消操作 | 内存使用稳定，无泄漏 |
| 资源清理 | 1. 取消生成<br>2. 检查资源释放 | 所有资源正确释放 |

### 4. 单元测试用例

```python
def test_batch_generation_cancel():
    """测试批量生成取消功能"""
    # 初始化
    tab = BatchGenTab()
    
    # 启动生成
    tab.on_generate_clicked()
    assert not tab.is_cancelling
    assert not tab.start_btn.isEnabled()
    
    # 执行取消
    tab.cancel_generation()
    assert tab.is_cancelling
    assert not tab.start_btn.isEnabled()
    assert not tab.cancel_btn.isEnabled()
    
    # 验证重复取消
    tab.cancel_generation()
    # 确保没有额外影响

def test_history_record_creation():
    """测试历史记录创建"""
    # 初始化
    tab = BatchGenTab()
    
    # 模拟图片保存
    record = {
        "timestamp": "2024-01-15 00:00:00",
        "params": {
            "prompt": "test prompt",
            "model": "test_model"
        },
        "image_path": "test.png"
    }
    
    # 触发记录创建
    tab.on_image_saved(record)
    
    # 验证记录
    history = tab.history_manager.get_records()
    assert len(history) == 1
    assert history[0]["image_paths"] == ["test.png"]

def test_ui_responsiveness():
    """测试UI响应性"""
    # 初始化
    tab = BatchGenTab()
    
    # 启动生成
    tab.on_generate_clicked()
    
    # 执行取消
    start_time = time.time()
    tab.cancel_generation()
    end_time = time.time()
    
    # 验证响应时间
    assert end_time - start_time < 0.1  # 响应时间应小于100ms
```

### 5. 历史记录测试

#### 5.1 记录保存测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 参数记录 | 1. 生成图片<br>2. 检查历史记录 | 完整保存所有生成参数 |
| 图片链接 | 1. 查看历史记录<br>2. 打开保存的图片 | 正确保存和显示图片路径 |

#### 5.2 历史操作测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 参数还原 | 1. 双击历史记录<br>2. 检查参数设置 | 准确还原历史参数设置 |
| 清空记录 | 1. 点击清空按钮<br>2. 确认操作 | 正确清空所有历史记录 |

### 6. 性能测试

#### 6.1 响应性能测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 界面响应 | 1. 生成过程中操作界面<br>2. 测试各个控件 | 界面保持响应，不出现卡顿 |
| 大量数据 | 1. 导入1000条提示词<br>2. 观察处理性能 | 在5秒内完成导入处理 |

#### 6.2 资源占用测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 内存使用 | 1. 监控内存占用<br>2. 执行批量生成 | 内存占用不超过500MB |
| CPU负载 | 1. 监控CPU使用率<br>2. 执行批量生成 | CPU峰值不超过50% |

### 7. 兼容性测试

#### 7.1 系统兼容测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| Windows | 1. 在Windows系统运行<br>2. 测试所有功能 | 功能正常，界面正确显示 |
| macOS | 1. 在macOS系统运行<br>2. 测试所有功能 | 功能正常，界面正确显示 |

#### 7.2 文件兼容测试
| 测试项 | 测试步骤 | 预期结果 |
|-------|---------|----------|
| 文本格式 | 1. 测试不同格式文本文件<br>2. 检查导入结果 | 正确处理各种文本格式 |
| Excel版本 | 1. 测试不同版本Excel文件<br>2. 检查导入结果 | 兼容主流Excel版本 |

## 设置界面测试

### 种子值设置测试
```python
def test_default_seed_setting(settings_tab, mock_config, monkeypatch):
    """测试默认种子值设置"""
    # 验证初始状态
    assert settings_tab.default_seed_spin.text() == ""  # 显示为空
    assert settings_tab.default_seed_spin.minimum() == 0  # 最小值为0
    assert settings_tab.default_seed_spin.maximum() == 2147483647
    
    # 测试保存空值
    settings_tab.default_seed_spin.clear()  # 清空值
    settings_tab.save_settings()
    assert "seed" not in mock_config.get("defaults", {})  # 空值不保存
    
    # 测试设置具体值
    settings_tab.default_seed_spin.setValue(42)
    settings_tab.save_settings()
    assert mock_config.get("defaults", {}).get("seed") == 42  # 保存具体值
    
    # 测试加载空值
    mock_config.config = {"defaults": {}}  # 清空设置
    settings_tab.load_settings()
    assert settings_tab.default_seed_spin.text() == ""  # 显示为空
```

测试要点：
1. 初始状态验证
   - 显示为空
   - 范围正确（0-2147483647）
   
2. 空值处理
   - 可以清空值
   - 空值不保存到配置
   
3. 具体值处理
   - 可以设置具体值
   - 具体值正确保存
   
4. 加载验证
   - 正确加载空值
   - 正确加载具体值
 
## 随机种子功能测试

### 测试用例

1. 随机种子UI测试
```python
def test_random_seed_behavior():
    """测试随机种子复选框行为"""
    # 初始状态检查
    assert not tab.random_seed_check.isChecked()
    assert tab.seed_spin.isEnabled()
    
    # 选中随机种子
    tab.random_seed_check.setChecked(True)
    assert not tab.seed_spin.isEnabled()
    assert not tab.seed_spin.text()
    
    # 取消选中
    tab.random_seed_check.setChecked(False)
    assert tab.seed_spin.isEnabled()
```

2. 种子值生成测试
```python
def test_seed_generation():
    """测试种子值生成"""
    # 使用随机种子
    tab.random_seed_check.setChecked(True)
    tab.batch_spin.setValue(4)
    params = tab.get_generation_params()
    seeds = params["seeds"]
    assert len(seeds) == 4
    assert len(set(seeds)) == 4  # 确保所有种子值都不相同
    
    # 使用固定种子
    tab.random_seed_check.setChecked(False)
    tab.seed_spin.setValue(12345)
    params = tab.get_generation_params()
    seeds = params["seeds"]
    assert len(seeds) == 4
    assert len(set(seeds)) == 1  # 确保所有种子值相同
    assert seeds[0] == 12345
```

3. 清空按钮测试
```python
def test_clear_seed():
    """测试清空种子值"""
    tab.seed_spin.setValue(12345)
    assert tab.seed_spin.value() == 12345
    
    # 点击清空按钮
    tab.clear_seed_btn.click()
    assert not tab.seed_spin.text()
```

## 历史记录管理界面测试

### 拖放排序功能测试

#### 基本功能测试

1. 拖放操作
   - [ ] 点击并按住任意行，确认可以开始拖动
   - [ ] 拖动时观察是否有清晰的视觉指示器
   - [ ] 释放鼠标后，记录应移动到目标位置

2. 内容完整性
   - [ ] 拖放后检查所有列的内容是否完整保留
   - [ ] 确认缩略图正确显示
   - [ ] 验证复选框状态是否保持

3. 视觉反馈
   - [ ] 拖动时是否显示水平线指示器
   - [ ] 指示器两端是否有三角形标记
   - [ ] 拖动时行的背景是否有高亮效果

#### 边界条件测试

1. 特殊位置
   - [ ] 拖动到第一行
   - [ ] 拖动到最后一行
   - [ ] 拖动到当前位置（应该不发生变化）

2. 多行操作
   - [ ] 拖动时表格中有多行数据
   - [ ] 表格滚动时的拖放操作
   - [ ] 快速连续拖放操作

#### 数据同步测试

1. 历史记录
   - [ ] 拖放后检查历史记录文件是否正确更新
   - [ ] 关闭并重新打开界面，确认顺序保持不变

2. 界面同步
   - [ ] 拖放后其他标签页中的历史记录是否同步更新
   - [ ] 验证历史记录更新信号是否正确触发

#### 异常处理测试

1. 错误情况
   - [ ] 拖放过程中关闭窗口
   - [ ] 拖放时文件被外部修改
   - [ ] 拖放到无效位置

2. 恢复机制
   - [ ] 拖放失败时是否恢复原始状态
   - [ ] 错误发生时是否有适当的提示

#### 性能测试

1. 响应性
   - [ ] 拖动大量记录时的性能
   - [ ] 包含多个缩略图时的性能
   - [ ] 快速拖放操作的响应速度

2. 内存使用
   - [ ] 长时间拖放操作的内存占用
   - [ ] 大量图片时的内存管理
 
# 测试文档

## 种子值输入测试
### 功能测试
1. 基本输入测试
   - [ ] 输入有效数字（如：123456）
   - [ ] 输入空值
   - [ ] 输入非数字字符
   - [ ] 输入小于1的数字
   - [ ] 输入大于9999999999的数字

2. 边界值测试
   - [ ] 输入值：1（最小值）
   - [ ] 输入值：9999999999（最大值）
   - [ ] 输入值：9999999998（最大值-1）
   - [ ] 输入值：2（最小值+1）

3. 特殊情况测试
   - [ ] 复制粘贴超长数字
   - [ ] 复制粘贴非数字文本
   - [ ] 复制粘贴混合内容（数字+文字）

4. 保存加载测试
   - [ ] 保存空值后重新加载
   - [ ] 保存有效值后重新加载
   - [ ] 保存最大值后重新加载
   - [ ] 保存最小值后重新加载

### 预期结果
1. 输入验证
   - 空值：允许，表示使用随机种子
   - 非数字：自动移除非数字字符
   - 范围外：自动调整到最近的有效值
   - 有效值：正常显示

2. 数据处理
   - 保存：正确保存有效的种子值
   - 加载：正确显示已保存的种子值
   - 清空：清除输入内容，恢复为空值状态

3. 界面响应
   - 输入提示正确显示
   - 工具提示正确显示
   - 清空按钮功能正常
 
## API错误处理测试

### 测试场景

1. 重试机制测试
   - 测试目的：验证API请求失败时的重试功能
   - 测试步骤：
     1. 使用无效的API密钥发起请求
     2. 观察重试次数和等待时间
     3. 确认最终错误信息
   - 预期结果：
     - 应进行3次重试
     - 每次重试间隔递增
     - 最终抛出适当的错误信息

2. 网络错误测试
   - 测试目的：验证网络问题时的错误处理
   - 测试步骤：
     1. 断开网络连接
     2. 发起API请求
     3. 观察错误处理过程
   - 预期结果：
     - 显示网络连接失败提示
     - 进行重试
     - 记录详细错误日志

3. API限制测试
   - 测试目的：验证API限制时的处理
   - 测试步骤：
     1. 快速发送多个请求触发限制
     2. 观察429错误处理
   - 预期结果：
     - 显示限制提示
     - 等待适当时间后重试
     - 记录警告日志

### 测试用例

```python
def test_api_retry_mechanism():
    """测试API重试机制"""
    api = SiliconFlowAPI("invalid_key")
    try:
        api.generate_image(prompt="test", model="test")
        assert False, "应该抛出异常"
    except Exception as e:
        assert "API请求失败" in str(e)
        # 检查日志中的重试记录
```
 
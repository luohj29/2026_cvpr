# AI图片数据抓取工具

## 项目结构

- `jimeng.py` - 即梦AI图片抓取主脚本
- `sora.py` - Sora AI图片抓取脚本  
- `utils.py` - 公共工具函数库
- `test.py` - 测试脚本

## 快速使用

### 1. 抓取数据
```bash
python jimeng.py
```

### 2. 去重处理
```python
from utils import filter_duplicate_from_json
filter_duplicate_from_json("jimeng_new_data.json", "jimeng_data_dedup.json")
```

### 3. 批量下载图片
```python
from utils import download_images_from_json
download_images_from_json("jimeng_data_dedup.json", "jimeng_final.json", "jimeng_images")
```

## 主要函数

### 从 jimeng.py 搬运到 utils.py 的函数：

- `pattern_match(driver, wait, patterns)` - 查找CSS选择器匹配的元素
- `pattern_click(driver, wait, item)` - JavaScript点击元素
- `fetch_text(driver, wait, TEXT_PATTERN)` - 提取页面文本
- `fetch_imgsrc(driver, wait, img_pattern)` - 提取图片URL
- `smart_scroll(driver)` - 智能滚动页面
- `save_to_json(data, filename)` - 追加保存JSON数据
- `load_data_from_json(filename)` - 加载JSON数据

### 其他工具函数：

- `filter_duplicate_from_json()` - 根据description去重
- `download_image()` - 下载单个图片
- `download_images_from_json()` - 批量下载图片
- `append_json()` - 追加数据到JSON文件

## 安装依赖

```bash
pip install selenium webdriver-manager requests
```

## 注意事项

- `jimeng.py` 的主函数代码保持不变，只是将函数定义移到了 `utils.py`
- 使用 `from utils import *` 导入所有工具函数
- 支持断点续传和智能去重
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from utils import (
    pattern_match, pattern_click, fetch_text, fetch_imgsrc, 
    smart_scroll, save_to_json, load_data_from_json
)
import time
import random

# ---------- 配置 ----------
START_URL = "https://jimeng.jianying.com/ai-tool/home"
OUT_IMG_PATTERN = "img.cover-s13ruV"
IN_IMG_PATTERN = ".image-C3mkAg"
TEXT_PATTERN = ".prompt-value-container-HNplhY"
EXIT_BUTTON_PATTERN = "icon-button-4AcBCE close-button-kyGUFo"
SCROLL_PAUSE = 1.2                                        # 每次滚动后等待时间
MAX_SCROLL_STEPS = 60                                     # 最大滚动次数（防止无限运行）
NO_NEW_LIMIT = 3                                          # 连续多少次没有新图片就停止
OUTPUT_JSON = "jimeng_new_data.json"
HEADLESS = True                                           # 是否无头

def setup_driver(headless=True):
    """
    设置并初始化Chrome浏览器驱动
    
    Args:
        headless: 是否启用无头模式
        
    Returns:
        tuple: (driver, wait) WebDriver实例和WebDriverWait实例
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)
    
    return driver, wait

def scrape_jimeng_images(max_scroll_steps=MAX_SCROLL_STEPS, no_new_limit=NO_NEW_LIMIT, output_file=OUTPUT_JSON):
    """
    抓取即梦AI图片和描述数据的主函数
    
    Args:
        max_scroll_steps: 最大滚动次数
        no_new_limit: 连续无新数据的限制次数
        output_file: 输出JSON文件路径
    """
    # 初始化浏览器
    driver, wait = setup_driver(headless=HEADLESS)
    
    try:
        # 访问网站
        driver.get(START_URL)
        
        # 加载现有数据，避免重复抓取
        existing_data = load_data_from_json(output_file)
        existing_descriptions = {item["description"] for item in existing_data if "description" in item}
        print(f"已加载 {len(existing_data)} 条现有数据，包含 {len(existing_descriptions)} 个唯一描述。")
        
        # 初始化抓取变量
        scroll_steps = 0
        no_new_count = 0
        data = []
        dict_set = set(existing_descriptions)
        
        # 主抓取循环
        while scroll_steps < max_scroll_steps and no_new_count < no_new_limit:
            scroll_steps += 1
            
            # 滚动页面加载更多内容
            smart_scroll(driver)
            time.sleep(SCROLL_PAUSE + random.uniform(0.2, 0.8))
            
            # 获取所有图片元素
            items = pattern_match(driver, wait, OUT_IMG_PATTERN)
            
            last_count = len(dict_set)
            print(f"滚动步骤 {scroll_steps}, 当前检测到 img 数量: {len(items)}, 已收集描述数: {len(dict_set)}")
            
            # 处理每个图片元素
            for i, item in enumerate(items):
                try:
                    if i == 0: 
                        continue  # 跳过第一个元素
                    
                    print(f"处理第 {i} 个图片...")
                    
                    # 点击图片打开详情页
                    pattern_click(driver, wait, item)
                    print("点击成功")
                    
                    # 提取图片URL和描述
                    img_src = fetch_imgsrc(driver, wait, IN_IMG_PATTERN)
                    description = fetch_text(driver, wait, TEXT_PATTERN)
                    print(f"描述: {description}")
                    
                    # 检查是否重复
                    if description in dict_set:
                        print("发现重复数据，跳过")
                        continue
                    else:
                        dict_set.add(description)
                    
                    # 添加到数据列表
                    data.append({
                        "id": len(dict_set),
                        "description": description,
                        "img_src": img_src
                    })
                    
                    # 关闭详情页
                    exit_item = driver.find_element(By.CSS_SELECTOR, EXIT_BUTTON_PATTERN)
                    pattern_click(driver, wait, exit_item)
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"处理第 {i} 个图片时出错: {e}")
                    continue
            
            # 检查是否有新数据
            if len(dict_set) == last_count:
                no_new_count += 1
            else:
                no_new_count = 0  # 重置计数器
                
            # 如果数据量达到限制，停止抓取
            if len(dict_set) > 2000:
                print("数据量达到2000条，停止抓取")
                break
        
        # 保存抓取的数据
        if data:
            save_to_json(data, output_file)
            print(f"✅ 本次抓取完成，共获取 {len(data)} 条新数据")
        else:
            print("⚠️ 本次抓取未获取到新数据")
            
    except Exception as e:
        print(f"❌ 抓取过程中出现错误: {e}")
    finally:
        # 确保浏览器关闭
        driver.quit()
        print("浏览器已关闭")

if __name__ == "__main__":
    # 运行主抓取函数
    scrape_jimeng_images()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils import *
import json
import time
import random
import os

# ---------- 配置 ----------
START_URL = "https://jimeng.jianying.com/ai-tool/home"
OUT_IMG_PATTERN = "img.cover-s13ruV"
IN_IMG_PATTERN = ".image-C3mkAg"
TEXT_PATTERN = ".prompt-value-container-HNplhY"
EXIT_BUTTON_PATTERN = "icon-button-4AcBCE close-button-kyGUFo"
SCROLL_PAUSE = 1.2                                        # 每次滚动后等待时间
MAX_SCROLL_STEPS = 60                                     # 最大滚动次数（防止无限运行）
NO_NEW_LIMIT = 3                                     # 连续多少次没有新图片就停止
OUTPUT_JSON = "images_data.json"
HEADLESS = True                                           # 是否无头
web_url = "https://jimeng.jianying.com/ai-tool/home"

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get(web_url)
wait = WebDriverWait(driver, 10)


def pattern_match(driver, wait, patterns):
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, patterns)))
    items = driver.find_elements(By.CSS_SELECTOR, patterns)
    return items


def pattern_click(driver, wait, item):
    driver.execute_script("arguments[0].click();", item)


def fetch_text(driver, wait, TEXT_PATTERN=".prompt-value-container-HNplhY"):
    """
    从详情页中提取描述文字
    - 自动等待元素出现
    - 捕获异常并返回 None
    """
    try:
        # 等待元素加载完成（最多等待10秒）
        elem = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, TEXT_PATTERN))
        )

        # 获取并清理文本
        text = elem.text.strip()
        if not text:
            print("⚠️ 描述元素存在但内容为空。")
            return None

        return text

    except TimeoutException:
        print(f"❌ 等待 {TEXT_PATTERN} 超时，未找到描述。")
        return None
    except NoSuchElementException:
        print(f"❌ 页面上未找到 {TEXT_PATTERN} 元素。")
        return None


def fetch_imgsrc(driver, wait, img_pattern=IN_IMG_PATTERN):
    """
    从指定元素中提取图片的 src
    - 支持 item 本身是 img 或外层容器
    - 自动尝试 src / data-src 属性
    """
    try:
        # 等待元素加载完成（最多等待10秒）
        elem = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, img_pattern))
        )

        # 获取并清理图片源
        img_src = elem.get_attribute("src") or elem.get_attribute("data-src")
        if not img_src:
            print("⚠️ 图片元素存在但没有 src 或 data-src 属性。")
            return None

        return img_src

    except TimeoutException:
        print(f"❌ 等待 {img_pattern} 超时，未找到描述。")
        return None
    except NoSuchElementException:
        print(f"❌ 页面上未找到 {img_pattern} 元素。")
        return None

# 使用附加方法将list保存为json文件
def save_to_json(data, filename="images_data.json"):
    # 如果文件存在，先读取现有数据
    existing_data = []
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ 读取现有文件失败，将创建新文件: {e}")
            existing_data = []
    
    # 合并现有数据和新数据
    if isinstance(existing_data, list):
        existing_data.extend(data)
    else:
        existing_data = data
    
    # 写入合并后的数据
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 数据已追加保存到 {filename}，共 {len(existing_data)} 条记录")


def load_data_from_json(filename="images_data.json"):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ 读取现有文件失败，将创建新文件: {e}")
            existing_data = []
    else:
        existing_data = []
    return existing_data


def smart_scroll(driver):
    # 自动寻找滚动容器
    containers = driver.find_elements(By.XPATH, "//*[contains(@style,'overflow') or contains(@class,'scroll')]")
    for c in containers:
        try:
            scroll_height = driver.execute_script("return arguments[0].scrollHeight - arguments[0].clientHeight;", c)
            if scroll_height > 100:  # 有滚动条的容器
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", c)
                print("✅ 已滚动容器：", c.get_attribute("class"))
                return True
        except Exception:
            continue

    # 兜底方案：尝试滚动 window
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    print("⚠️ 未找到滚动容器，退回到 window 滚动")
    return False

existing_data = load_data_from_json("jimeng_new_data.json")
existing_descriptions = {item["description"] for item in existing_data if "description" in item}
print(f"已加载 {len(existing_data)} 条现有数据，包含 {len(existing_descriptions)} 个唯一描述。")

scroll_steps = 0
no_new_count = 0
data = []
dict_set = set(existing_descriptions)

while scroll_steps < MAX_SCROLL_STEPS and no_new_count < NO_NEW_LIMIT:
    scroll_steps += 1

    # 先滚到底部以触发加载（可以按需改成小步滚动）
    smart_scroll(driver)
    time.sleep(SCROLL_PAUSE + random.uniform(0.2, 0.8))              
    items = pattern_match(driver, wait, OUT_IMG_PATTERN)

    last_count = len(dict_set)
    print(f"滚动步骤 {scroll_steps}, 当前检测到 img 数量: {len(items)}, 已收集描述数: {len(dict_set)}")
    for i, item in enumerate(items):
        try:
            if i == 0: continue
            print("item:", i)
            pattern_click(driver, wait, item)
            print("click success")
            img_src = fetch_imgsrc(driver, wait)
            description = fetch_text(driver, wait)
            print(description)
            
            if description in dict_set:
                print("duplicate, skip")
                continue
            else :
                dict_set.add(description)
                
            data.append({
                "id": len(dict_set),
                "description": description,
                "img_src": img_src
            })
            
            exit_item = driver.find_element(By.CSS_SELECTOR, EXIT_BUTTON_PATTERN)
            pattern_click(driver, wait, exit_item)
            time.sleep(5)
            
        except Exception as e:
            print(f"[{i+1}] Error: {e}")
            continue
        
    if len(dict_set) == last_count:
        no_new_count += 1
    if len(dict_set) > 2000:
        break

save_to_json(data, "jimeng_new_data.json")
driver.quit()

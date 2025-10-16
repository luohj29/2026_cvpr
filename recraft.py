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

def fetch_by_imgTag(driver, wait):
    try:
        elem = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img"))
        )
        data = []
        imgs = driver.find_elements(By.XPATH, "//img[contains(@src, 'img.recraft.ai')]")
        for img in imgs:
            print(img.get_attribute("src"))
            img_src = img.get_attribute("src") or img.get_attribute("data-src")
            print(img.get_attribute("alt"))
            description = img.get_attribute("alt").strip()
            data.append({
                "description": description,
                "img_src": img_src
            })
        return data
    except TimeoutException:
        print(f"❌ 等待 img 超时，未找到描述或者图片来源。")
        return []
    
#config ========================================
START_URL = "https://www.recraft.ai/community"
OUT_IMG_PATTERN = "img.cover-s13ruV"
IN_IMG_PATTERN = ".image-C3mkAg"
TEXT_PATTERN = ".prompt-value-container-HNplhY"
EXIT_BUTTON_PATTERN = "icon-button-4AcBCE close-button-kyGUFo"
SCROLL_PAUSE = 8                                       # 每次滚动后等待时间
MAX_SCROLL_STEPS = 60                                     # 最大滚动次数（防止无限运行）
NO_NEW_LIMIT = 3                                     # 连续多少次没有新图片就停止
OUTPUT_JSON = "recraft_images_data.json"
HEADLESS = True                                           # 是否无头


options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get(START_URL)
wait = WebDriverWait(driver, 10)

existing_data = load_data_from_json(OUTPUT_JSON)
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
    items = fetch_by_imgTag(driver, wait)

    last_count = len(dict_set)
    print(f"滚动步骤 {scroll_steps}, 当前检测到 img 数量: {len(items)}, 已收集描述数: {len(dict_set)}")
    for i, item in enumerate(items):
        if item["description"] in dict_set:
            print(f"描述已存在，跳过: {item['description']}")
            continue
        if not item["img_src"] or not item["description"]:
            print(f"⚠️ 跳过无效数据: {item}")
            continue
        print(f"新描述: {item['description']}, 图片链接: {item['img_src']}")
        data.append({
            "id": len(dict_set),
            "description": item["description"],
            "img_src": item["img_src"]
        })
        dict_set.add(item["description"])
        
    if len(dict_set) == last_count:
        no_new_count += 1
    if len(dict_set) > 2000:
        break

save_to_json(data, OUTPUT_JSON)
driver.quit()


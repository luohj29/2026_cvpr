from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

# 目标网址
web_url = "https://jimeng.jianying.com/ai-tool/home"

# 配置Chrome选项（无头模式）
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

driver.get(web_url)

# 等待页面加载完成（确保图片加载）
wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".img_container img")))

# 获取所有图片容器
img_divs = driver.find_elements(By.CSS_SELECTOR, ".img_container")

data = []

for idx, div in enumerate(img_divs):
    try:
        # 提取图片URL
        img = div.find_element(By.TAG_NAME, "img")
        img_src = img.get_attribute("src")

        # 点击进入详情页
        driver.execute_script("arguments[0].click();", div)

        # 等待描述加载
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".description, .desc, p")))

        # 尝试获取描述文本（根据网页结构自行调整选择器）
        desc_elem = driver.find_element(By.CSS_SELECTOR, ".description, .desc, p")
        description = desc_elem.text.strip()

        # 保存结果
        data.append({
            "description": description,
            "img_src": img_src
        })

        print(f"[{idx+1}] {description[:30]}...")

        # 返回主页
        driver.back()
        time.sleep(1)

    except Exception as e:
        print(f"[{idx+1}] error: {e}")
        # 如果点击无效或未加载完全，可选择刷新或跳过
        driver.get(web_url)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".img_container img")))
        img_divs = driver.find_elements(By.CSS_SELECTOR, ".img_container")

# 保存为 JSON 文件
with open("images_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

driver.quit()
print("✅ Done! Saved to images_data.json")

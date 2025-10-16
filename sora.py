from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    InvalidSessionIdException,
    StaleElementReferenceException,
)
from utils import *
import json
import time
import random
import os

# ------------------ 配置 ------------------
START_URL = "https://sora.chatgpt.com/explore/images"
USER_DATA_DIR = "/home/rogers/.config/google-chrome/Default"
SCROLL_PAUSE = 8
MAX_SCROLL_STEPS = 60
NO_NEW_LIMIT = 3
OUTPUT_JSON = "sora_images_data.json"
# 详情页图片选择器（尽量通用，页面上第一张有 src 的 img）
IN_IMG_XPATH = "//img[contains(@src, 'http')][1]"
# 主页面中定位目标 img 的 xpath（根据你的 fetch_by_imgTag 逻辑调整）
MAIN_IMG_XPATH = "//img[contains(@src, 'https://videos.openai.com')]"
# -------------------------------------------

options = Options()
# 你使用的是 attach 模式（手动启动 chrome --remote-debugging-port=9222）
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

# 启动 driver（attach 模式）
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

# 打开起始页（attach 情况下可能已经在页面，但安全起见再打开）
# try:
#     driver.get(START_URL)
# except Exception:
#     # 如果 attach 的 chrome 已经在正确页面，这里可能抛异常，忽略
#     pass

# 确保页面加载一会儿
time.sleep(5)

# 加载已存在数据并构建去重集合（以 (description, img_src) 为 key）
existing_data = load_data_from_json(OUTPUT_JSON)
existing_keys = set()
for item in existing_data:
    desc = item.get("description", "")
    src = item.get("img_src")
    existing_keys.add((desc, src))

print(f"已加载 {len(existing_data)} 条现有数据，包含 {len(existing_keys)} 个唯一记录。")

scroll_steps = 0
no_new_count = 0
collected = []
keys_set = set(existing_keys)


def fetch_by_imgTag(driver, wait):
    """返回主页面上我们关心的 img 元素列表（稳定等待后抓取）。"""
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "img")))
        imgs = driver.find_elements(By.XPATH, MAIN_IMG_XPATH)
        return imgs
    except (TimeoutException, NoSuchElementException):
        print("❌ 等待 img 超时，未找到图片元素。")
        return []


while scroll_steps < MAX_SCROLL_STEPS and no_new_count < NO_NEW_LIMIT:
    scroll_steps += 1

    # 智能滚动（请在 utils.smart_scroll 中实现可控滚动）
    try:
        smart_scroll(driver)
    except Exception as e:
        print("滚动出错：", e)

    time.sleep(SCROLL_PAUSE + random.uniform(0.2, 0.8))

    items = fetch_by_imgTag(driver, wait)
    last_count = len(keys_set)

    print(f"滚动步骤 {scroll_steps}, 当前检测到 img 数量: {len(items)}, 已收集记录数: {len(keys_set)}")

    for idx, item in enumerate(items):
        try:
            # 在主页面拿到跳转 href（用 JS 更稳，不依赖于元素层级会因为 DOM 变动失效）
            try:
                h_ref = driver.execute_script(
                    "let a = arguments[0].closest('a'); return a ? a.href : null;",
                    item,
                )
            except Exception:
                h_ref = None

            if not h_ref:
                print("⚠️ 未找到链接，跳过。")
                continue

            # 在新 tab 中打开详情页（避免直接在原 tab 导致页面被重写）
            driver.execute_script("window.open('about:blank');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(h_ref)

            # 等待详情页加载图片——给足够时间
            detail_wait = WebDriverWait(driver, 10)
            try:
                img_elem = detail_wait.until(EC.presence_of_element_located((By.XPATH, IN_IMG_XPATH)))
            except TimeoutException:
                print("❌ 详情页图片加载超时，关闭标签并继续。")
                # 关闭并回到主页
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)
                continue

            # 获取图片链接
            img_src = img_elem.get_attribute("src") or img_elem.get_attribute("data-src")

            # 获取描述按钮文本（更宽松的 class 匹配）
            buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'truncate')]")
            description = ""
            if len(buttons) == 1:
                description = buttons[0].text.strip()
            elif len(buttons) > 1:
                # 如果有多个，选择第一个非空的文本
                for b in buttons:
                    t = b.text.strip()
                    if t:
                        description = t
                        break

            if not description:
                # 尝试用其他候选节点抓描述（常见的 container）
                try:
                    p = driver.find_element(By.XPATH, "//p[normalize-space(string()) != '']")
                    description = p.text.strip()
                except Exception:
                    pass

            key = (description, img_src)
            if key not in keys_set and description:
                keys_set.add(key)
                collected.append({"description": description, "img_src": img_src})
                print(f"  ✅ 新记录: {description[:40]}..., 图片链接: {img_src}")
            else:
                print("  ⚠️ 已存在或缺失描述，跳过。")

        except InvalidSessionIdException:
            print("🚨 会话无效：浏览器已断开连接。终止爬取。")
            # 尝试干净退出
            try:
                driver.quit()
            except Exception:
                pass
            raise

        except StaleElementReferenceException:
            print("⚠️ 元素在遍历过程中失效，跳过此元素。")

        except Exception as e:
            print(f"❌ 异常: {e}")

        finally:
            # 无论成功失败都关闭详情页并回到主窗口（仅当新 tab 存在时）
            # 返回START_URL
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)
                

    # 更新 no_new_count 逻辑
    if len(keys_set) == last_count:
        no_new_count += 1
    else:
        no_new_count = 0

    # 采集上限保护
    if len(keys_set) > 2000:
        print("达到上限，停止采集。")
        break

# 合并并写回文件
if collected:
    final = existing_data + collected
    save_to_json(final, OUTPUT_JSON)
    print(f"已保存 {len(collected)} 条新数据到 {OUTPUT_JSON}")
else:
    print("没有新数据需要保存。")

# 结束时确保退出 driver
try:
    driver.quit()
except Exception:
    pass

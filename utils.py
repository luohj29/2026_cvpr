import json
import os
import requests
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def filter_duplicate_from_json(input_path, output_path):
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 根据description去重
        seen = set()
        unique_data = []
        for item in data:
            desc = item.get('description')
            if desc and desc not in seen:
                seen.add(desc)
                unique_data.append(item)
        # 将去重后的数据写回文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(unique_data, f, ensure_ascii=False, indent=4)
        print(f"Filtered duplicates. {len(data) - len(unique_data)} duplicates removed.")
    except Exception as e:
        print(f"Error processing {input_path}: {e}")

def download_image(img_url, save_dir="images", file_name=None):
    """
    从URL下载图片到本地
    :param img_url: 图片URL
    :param save_dir: 保存的文件夹（默认 images）
    :param file_name: 文件名（可选，自动从URL推断）
    :return: 保存路径
    """
    os.makedirs(save_dir, exist_ok=True)

    # 如果未指定文件名，则从URL中提取
    if file_name is None:
        file_name = img_url.split("/")[-1].split("?")[0]  # 去掉参数
    save_path = os.path.join(save_dir, file_name)

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/125.0.0.0 Safari/537.36"
        }

        # 发送请求
        response = requests.get(img_url, headers=headers, stream=True, timeout=15)
        response.raise_for_status()

        # 写入文件（二进制）
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        print(f"✅ 已保存: {save_path}")
        return save_path

    except Exception as e:
        print(f"❌ 下载失败: {img_url}\n  错误: {e}")
        return None


def append_json(data_list, json_path):
    if os.path.exists(json_path):
        existing_data = json.load(open(json_path, "r", encoding="utf-8"))
        if isinstance(existing_data, list):
            existing_data.extend(data_list)
        else:
            existing_data = data_list
    else:
        existing_data = data_list
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 数据已追加保存到 {json_path}，共 {len(existing_data)} 条记录")
    
def download_images_from_json(json_path, out_json_path, save_dir="images"):
    items = json.load(open(json_path, "r", encoding="utf-8"))
    new_data = []
    for idx, item in enumerate(items):
        if idx % 20 == 0:
            append_json(new_data, out_json_path)
            new_data = []
            time.sleep(15)
        img_url = item.get("img_src")
        if img_url:
            file_name = "jimeng{:04d}".format(idx) + os.path.splitext(img_url.split("/")[-1].split("?")[0])[-1]
            download_image(img_url, save_dir=save_dir, file_name=file_name)
            new_data.append({"id": idx, "description": item.get("description"), "img_src": img_url, "local_path": os.path.join(save_dir, file_name)})
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 下载完成，信息已保存到 {out_json_path}")

# ========== 从 jimeng.py 搬运的函数 ==========

def pattern_match(driver, wait, patterns):
    """
    等待并查找匹配CSS选择器的所有元素
    """
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, patterns)))
    items = driver.find_elements(By.CSS_SELECTOR, patterns)
    return items


def pattern_click(driver, wait, item):
    """
    使用JavaScript点击元素
    """
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


def fetch_imgsrc(driver, wait, img_pattern=".image-C3mkAg"):
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


def smart_scroll(driver):
    """
    智能滚动页面
    """
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

def save_to_json(data, filename="images_data.json"):
    """
    使用附加方法将list保存为json文件
    """
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
    """
    从JSON文件加载数据
    """
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

if __name__ == "__main__":
    # 示例用法
    # filter_duplicate_from_json("images_data.json", "images_data_dedup.json")
    # download_images_from_json("jimeng_images_data_dedup.json", "jimeng_images_data_final.json", save_dir="jimeng_images")
    in_json= "jimeng_new_data.json"
    # out_json = "jimeng_inew_data_filtered.json"
    final_json = "jimeng_new_data_final1.json"
    my_save_dir = "jimeng_images_new"
    # filter_duplicate_from_json(in_json, out_json)
    download_images_from_json(in_json, final_json, save_dir=my_save_dir)


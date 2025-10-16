import json
import os
import requests
import time

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
        
if __name__ == "__main__":
    # 示例用法
    # filter_duplicate_from_json("images_data.json", "images_data_dedup.json")
    # download_images_from_json("jimeng_images_data_dedup.json", "jimeng_images_data_final.json", save_dir="jimeng_images")
    in_json= "jimeng_new_data.json"
    # out_json = "jimeng_inew_data_filtered.json"
    final_json = "jimeng_new_data_final.json"
    my_save_dir = "jimeng_images_new"
    # filter_duplicate_from_json(in_json, out_json)
    download_images_from_json(in_json, final_json, save_dir=my_save_dir)


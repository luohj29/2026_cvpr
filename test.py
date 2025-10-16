import selenium
import requests
#use senlenium to open a web to download all the img files to a json
web_url = "https://jimeng.jianying.com/ai-tool/home"

def fetch_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

pattern_css = 

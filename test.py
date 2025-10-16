# full_cookie_inject_and_check.py
import time
import browser_cookie3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

START_URL = "https://sora.chatgpt.com"

opts = Options()
# 不要用 headless
# opts.add_argument("--headless=new")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)

driver = uc.Chrome(options=opts)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
})

driver.get(START_URL)
time.sleep(2)

# 从系统 Chrome 读取 cookie（包含 HttpOnly）
cj = browser_cookie3.chrome(domain_name="sora.chatgpt.com")
print("读取到 cookie 数量：", len(list(cj)))

for ck in cj:
    try:
        cookie = {"name": ck.name, "value": ck.value}
        driver.add_cookie(cookie)
    except Exception as e:
        print("add_cookie error:", e)

driver.refresh()
time.sleep(5)
print("刷新后 title:", driver.title)
print("当前 cookies:", driver.get_cookies())
# 检查页面是否为 Cloudflare 验证页面（简单检查）
src = driver.page_source.lower()
if "checking your browser" in src or "turnstile" in src or "captcha" in src:
    print("页面可能仍被 Cloudflare 验证拦截，需要人工干预或其他方案。")
else:
    print("看起来页面已通过或正常加载。")

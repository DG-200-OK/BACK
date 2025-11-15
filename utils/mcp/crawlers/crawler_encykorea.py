import time
import urllib.parse
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def download_image(url):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"이미지 다운로드 실패: {e}")
        return None


def crawler_encykorea(keyword: str):
    encoded = urllib.parse.quote(keyword)
    url = f"https://encykorea.aks.ac.kr/Article/Search/{encoded}"

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    driver.get(url)
    time.sleep(2)

    titles = driver.find_elements(By.CSS_SELECTOR, "div.title")
    detail_url = None
    for idx, div in enumerate(titles, 1):
        raw_title = div.text.strip()
        clean_title = re.sub(r"\(.*?\)", "", raw_title).strip()
        if clean_title.replace(" ", "") == keyword.replace(" ", ""):
            parent_a = div.find_element(By.XPATH, "./ancestor::a")
            detail_url = parent_a.get_attribute("href")
            break

    if not detail_url:
        driver.quit()
        return {
            "error": "EncyKorea에서 결과 없음",
            "image_url": None,
            "alt": None,
            "description": None,
        }

    driver.get(detail_url)
    time.sleep(2)

    # img_elem = WebDriverWait(driver, 5).until(
    #     EC.presence_of_element_located((By.CSS_SELECTOR, "img"))
    # )

    img_elem = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'img[src*="devin.aks.ac.kr/image"]')
        )
    )

    image_url = img_elem.get_attribute("src")
    img_alt = img_elem.get_attribute("alt")
    desc_elem = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "p"))
    )
    description = desc_elem.text.strip()

    driver.quit()
    return [
        {
            "id": 1,
            "description": description,
            "alt": img_alt,
            "image_url": image_url,
        }
    ]

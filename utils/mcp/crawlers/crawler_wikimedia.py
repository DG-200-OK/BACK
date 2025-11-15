import time
import urllib.parse
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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


def crawler_wikimedia(keyword: str, limit: int = 1):
    encoded = urllib.parse.quote(keyword)  # 검색어 변환
    url = f"https://commons.wikimedia.org/w/index.php?search={encoded}&title=Special%3AMediaSearch&type=image"  # wikimedia에서 검색

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")  # 창 안보이게 하는 옵션
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    driver.get(url)
    time.sleep(2)

    # 자동 스크롤: limit에 맞춰 충분히 스크롤 다운
    scroll_pause_time = 3
    results = []

    last_height = driver.execute_script("return document.body.scrollHeight")
    retries = 0

    while True:
        # 🔹 스크롤 다운
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(scroll_pause_time)

        # 🔹 새 이미지 갱신 확인
        links = driver.find_elements(By.CSS_SELECTOR, "a.sdms-image-result")

        print(f"현재 {len(links)}개의 이미지 감지됨...")

        # 1️⃣ 충분히 모이면 중단
        if len(links) >= limit:
            print(f"✅ {limit}개 이상 로드됨, 스크롤 중단")
            break

        # 2️⃣ 더 이상 추가 안 생기면 3번 시도 후 중단
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            retries += 1
            if retries >= 3:
                print("⚠️ 더 이상 새로운 이미지가 로드되지 않아 중단합니다.")
                break
        else:
            retries = 0
        last_height = new_height

    # 🔹 로드 완료 후 다시 links 갱신
    links = driver.find_elements(By.CSS_SELECTOR, "a.sdms-image-result")

    # if not links:
    #     driver.quit()
    #     return [
    #         {
    #             "image_url": None,
    #             "alt": None,
    #             "description": None,
    #             "error": f"Wikimedia에서 '{keyword}' 결과 없음",
    #         }
    #     ]

    for idx, link in enumerate(links[:limit], start=3):
        img = link.find_element(By.TAG_NAME, "img")
        image_url = img.get_attribute("src")
        alt = img.get_attribute("alt")

        link.click()
        time.sleep(1)

        try:
            desc_elem = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".sdms-quick-view__description")
                )
            )
            description = desc_elem.text.strip()
        except Exception:
            description = "(설명 없음)"

        # description = driver.find_element(
        #     By.CSS_SELECTOR, ".sdms-quick-view__description"
        # ).text

        results.append(
            {
                "id": idx,
                "description": description,
                "alt": alt,
                "image_url": image_url,
            }
        )

    driver.quit()
    return results

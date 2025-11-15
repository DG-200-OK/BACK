import time
import urllib.parse
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def crawler_folkency(keyword: str):
    encoded = urllib.parse.quote(keyword)  # 검색어 변환
    url = f"https://folkency.nfm.go.kr/search/{encoded}"  # folkency에서 검색

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    driver.get(url)
    time.sleep(2)

    titles = driver.find_elements(By.CSS_SELECTOR, "h3.tit")

    detail_url = None
    for idx, h3 in enumerate(titles, 1):
        raw_title = h3.text.strip()
        clean_title = re.sub(r"\(.*?\)", "", raw_title).strip()

        if clean_title.replace(" ", "") == keyword.replace(" ", ""):
            parent_a = h3.find_element(By.XPATH, "./ancestor::a")
            detail_url = parent_a.get_attribute("href")
            break

    if not detail_url:
        driver.quit()
        return [
            {
                "error": "Folkency에서 결과 없음",
                "image_url": None,
                "description": "",
                "alt": None,
            }
        ]

    driver.get(detail_url)
    time.sleep(2)

    img_elem = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.thumb"))
    )
    image_url = img_elem.get_attribute("data-src")
    desc_elem = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "p.description"))
    )
    description = desc_elem.text.strip()

    driver.quit()

    return [
        {
            "id": 2,
            "description": description,
            "alt": None,  # folkency는 alt 없음
            "image_url": image_url,
        }
    ]


# if __name__ == "__main__":
#     test_keyword = input("검색어 입력: ")
#     print(f"\n[ 크롤러 테스트 시작: '{test_keyword}' ]\n")
#     results = crawler_folkency(test_keyword)

#     print("\n=== 크롤링 결과 ===")
#     for idx, item in enumerate(results, 1):
#         print(f"\n[{idx}]")
#         print(f"image_url: {item.get('image_url')}")
#         print(f"s3_url: {item.get('s3_url')}")
#         print(f"description: {item.get('description')[:100]}...")
#         print(f"error: {item.get('error')}")

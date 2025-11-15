# database.py
import os
import csv
import boto3
import sqlite3
import hashlib
import requests
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError, ClientError


def upload_image_to_s3(results):
    # 환경 변수 설정
    load_dotenv()
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    AWS_REGION = os.getenv("AWS_REGION")
    BUCKET_NAME = os.getenv("BUCKET_NAME")

    # boto3 클라이언트 생성
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION,
    )

    upload_count = 0

    for r in results:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            response = requests.get(r.get("image_url"), headers=headers, timeout=10)
            response.raise_for_status()
            image_bytes = response.content
        except Exception as e:
            print(f"이미지 다운로드 실패: {e}")
            continue

        id = r.get("id")
        query = r.get("query")
        search_id = make_search_id(query)
        file_name = f"{query}_{id}.jpg"
        s3_key = f"{search_id}/{file_name}"

        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=image_bytes,
                ContentType="image/jpeg",
            )

            # s3_url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
            upload_count = upload_count + 1
        except (NoCredentialsError, ClientError) as e:
            print(f"이미지 업로드 실패: {e}")

    print(f"총 {upload_count}개의 '{query}' 이미지 업로드 완료")


def save_results_to_csv(results):
    """크롤링 결과를 CSV 형태로 저장"""
    os.makedirs("results", exist_ok=True)
    csv_path = os.path.join("results", "results.csv")

    fieldnames = [
        "id",
        "query",
        "search_id",
        "source",
        "description",
        "alt",
        "image_url",
    ]
    write_header = not os.path.exists(csv_path)

    with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        for item in results:
            query = item.get("query")
            writer.writerow(
                {
                    "id": item.get("id"),
                    "query": query,
                    "search_id": make_search_id(query),
                    "source": item.get("source"),
                    "description": (item.get("description") or "").strip()[:200],
                    "alt": item.get("alt", ""),
                    "image_url": item.get("image_url", ""),
                }
            )

    print(f"✅ CSV 파일에 {len(results)}개 결과가 추가되었습니다. ({csv_path})")


# DB 보기
# python -c "from utils.mcp.database import show_all_results; show_all_results()"
# DB 비우기
# python -c "from utils.mcp.database import clear_all_results; clear_all_results()"


def save_results_to_db(results):
    conn = sqlite3.connect("crawler_results.db")
    cur = conn.cursor()

    # 테이블 생성
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            search_id INTEGER,
            source TEXT,
            description TEXT,
            alt TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    for item in results:
        query = item.get("query")
        search_id = make_search_id(query)
        source = item.get("source")
        description = (item.get("description") or "").strip()
        alt = (item.get("alt") or "").strip()
        image_url = item.get("image_url")

        cur.execute(
            """
            INSERT INTO results (query, search_id, source, description, alt, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (query, search_id, source, description, alt, image_url),
        )

    conn.commit()
    conn.close()
    print(f"✅ {source} 결과가 DB에 저장되었습니다.")


# import hashlib
def make_search_id(query: str) -> int:
    """SHA256 기반 안정 해시 → 앞 8자리만 int로 변환"""
    h = hashlib.sha256(query.encode("utf-8")).hexdigest()
    return int(h[:8], 16)


# DB 보기
def show_all_results():
    conn = sqlite3.connect("crawler_results.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT id, query, search_id, source, description, alt, image_url, created_at FROM results ORDER BY id DESC"
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("⚠️ 저장된 결과가 없습니다.")
        return

    print("\n=== 저장된 결과 목록 ===")
    for row in rows:
        print(
            f"ID: {row[0]} | Query: {row[1]} | Search_ID: {row[2]} | Source: {row[3]} | Description: {row[4]} | Alt: {row[5]} | Image URL: {row[6]}"
        )
    print("=============================================\n")


# DB 비우기
def clear_all_results():
    conn = sqlite3.connect("crawler_results.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM results")
    conn.commit()
    conn.close()
    print("✅ 모든 데이터가 삭제되었습니다.")


if __name__ == "__main__":
    show_all_results()

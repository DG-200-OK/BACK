import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from crawlers.crawler_encykorea import crawler_encykorea
from crawlers.crawler_folkency import crawler_folkency
from crawlers.crawler_wikimedia import crawler_wikimedia
from database import (
    save_results_to_csv,
    save_results_to_db,
    upload_image_to_s3,
)

# --------------------------------------------------------------------------------
# ✅ 이 파일 다른 곳에서 임포트해서 사용 하는 법
# --------------------------------------------------------------------------------
# from mcp import run_crawlers
# results = run_crawlers("김밥")


load_dotenv()
client = OpenAI(api_key=os.getenv("GPT_API"))

# --- 함수(도구) 정의 ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "crawler_encykorea",
            "description": "한국민족문화대백과사전에서 데이터를 수집합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색어"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crawler_folkency",
            "description": "한국민속대백과사전에서 데이터를 수집합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crawler_wikimedia",
            "description": "Wikimedia에서 이미지를 수집합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 3},  # limit hint
                },
                "required": ["query"],
            },
        },
    },
]


# --------------------------------------------------------------------------------
# ✅ 함수로 분리: 다른 파일에서 import해서 사용할 수 있는 진짜 핵심 함수
# --------------------------------------------------------------------------------
def run_crawlers(query: str):
    """키워드를 받아 모든 크롤러를 실행하고 결과 리스트를 반환"""

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an MCP controller that decides which crawler to run. "
                    "Always execute all three crawlers (encykorea, folkency, wikimedia) "
                    "for every query."
                ),
            },
            {"role": "user", "content": f"검색어: {query}"},
        ],
        tools=tools,
    )

    msg = response.choices[0].message
    all_results = []

    if msg.tool_calls:
        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments)
            target_number = 97

            if name == "crawler_encykorea":
                result = crawler_encykorea(args["query"])
            elif name == "crawler_folkency":
                result = crawler_folkency(args["query"])
            elif name == "crawler_wikimedia":
                result = crawler_wikimedia(args["query"], target_number)
            else:
                result = []

            # 결과 공통 필드 추가
            for r in result:
                r["query"] = query
                r["source"] = name.replace("crawler_", "")
                all_results.append(r)

    # 저장 기능
    save_results_to_csv(all_results)
    save_results_to_db(all_results)
    upload_image_to_s3(all_results)

    return all_results


# --------------------------------------------------------------------------------
# 🔧 스크립트 직접 실행 시 (python mcp.py)
# --------------------------------------------------------------------------------
if __name__ == "__main__":
    query = input("검색어 입력(Test): ")
    results = run_crawlers(query)

    print("\n=== 크롤링 완료 ===")
    print(f"총 {len(results)}개 수집됨.")
    for r in results:
        id = r.get("id")
        query = r.get("query")
        source = r.get("source")
        desc = (r.get("description") or "").strip()
        desc = desc[:30] + ("..." if len(desc) > 30 else "")
        print(f"[{id}] {query} | {source} | {desc}")

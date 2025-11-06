from fastapi import APIRouter
from starlette.responses import StreamingResponse  # 👈 StreamingResponse 임포트
from .. import crud
from ..schemas import crawler as crawler_schema

router = APIRouter(
    prefix="/crawler", # 이 라우터의 모든 경로는 /crawler로 시작
    tags=["crawler"]    # API 문서에서 "crawler" 태그로 그룹화
)

# API 1: 카테고리별 평가 점수 조회
@router.get("/score", response_model=crawler_schema.CrawlerScoreResponse)
def read_crawler_score():
    return crud.get_dummy_crawler_score()

# API 2: 개별 데이터 조회
@router.get("/data", response_model=crawler_schema.CrawlerDataResponse)
def read_crawler_data():
    return crud.get_dummy_crawler_data()

# ❗️ API 3: 크롤러 검색 요청 (실시간 스트리밍 버전)
@router.post("/search") # 👈 response_model을 제거해야 합니다.
async def request_crawler_search(request: crawler_schema.CrawlerSearchRequest):
    """
    크롤러 검색을 요청하고, 진행률을 SSE(Server-Sent Events)로 실시간 스트리밍합니다.
    """
    # crud의 스트리밍 함수를 StreamingResponse로 감싸서 반환합니다.
    return StreamingResponse(
        crud.stream_dummy_crawler_search(request=request),
        media_type="text/event-stream"  # 👈 브라우저에게 SSE임을 알림
    )
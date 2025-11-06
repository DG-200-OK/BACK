from pydantic import BaseModel
from typing import Optional

# API 1: /crawler/score 응답
class CrawlerScoreResponse(BaseModel):
    scoreA: int
    scoreC: int

# API 2: /crawler/data 응답
class CrawlerDataResponse(BaseModel):
    scoreA: int
    scoreC: int
    country: str
    category: str
    imageUrl: str

# API 3: /crawler/search 요청
class CrawlerSearchRequest(BaseModel):
    keyword: str

# API 3: /crawler/search 응답
class CrawlerSearchResponse(BaseModel):
    progress: int
    time: int
    speed: int

    class Config:
        # Pydantic 모델을 dict처럼 사용할 수 있게 함
        orm_mode = True
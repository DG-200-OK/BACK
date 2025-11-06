from pydantic import BaseModel
from typing import Optional

# API 4: /data/search 요청
class DataSearchRequest(BaseModel):
    category: str
    nation: str

# API 4: /data/search 응답
class DataSearchResponse(BaseModel):
    category: str
    image: str
    total_data_set: int # 명세서의 "total-data-set"을 Python 변수명(snake_case)으로 변경
    nation: str

    class Config:
        orm_mode = True
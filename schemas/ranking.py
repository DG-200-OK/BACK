from pydantic import BaseModel
from typing import List

class RankingData(BaseModel):
    username: str
    responseCount: int
    rank: int

class RankingResponse(BaseModel):
    success: bool
    responseData: List[RankingData]

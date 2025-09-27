from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import crud
from database import get_db
from schemas.ranking import RankingResponse

router = APIRouter()

@router.get("/", response_model=RankingResponse)
async def get_ranking(db: AsyncSession = Depends(get_db)):
    """사용자 랭킹을 조회합니다."""
    rankings = await crud.get_user_rankings(db)
    return {"success": True, "responseData": rankings}
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import crud
from database import get_db
from schemas.chart import ChartResponseV2, SingleChartResponse

router = APIRouter()

@router.get("/", response_model=ChartResponseV2)
async def get_chart_list(db: AsyncSession = Depends(get_db), page: int = Header(1), category: str | None = Header(None), search: str | None = Query(None)):
    """차트 데이터 목록 조회 API"""
    page_size = 4
    chart_data = await crud.get_chart_data_by_caption(db, page=page, page_size=page_size, category=category, search=search)
    return chart_data

@router.get("/{caption_id}", response_model=SingleChartResponse)
async def get_single_chart(caption_id: int, db: AsyncSession = Depends(get_db)):
    """단일 캡션에 대한 차트 데이터 조회 API"""
    caption_data = await crud.get_chart_data_for_single_caption(db, caption_id=caption_id)
    if not caption_data:
        raise HTTPException(status_code=404, detail="Caption not found")
    
    return SingleChartResponse(responseData=caption_data)

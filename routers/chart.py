from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import crud
from database import get_db
from schemas.chart import ChartResponseV2, SingleChartResponse, OverallWassersteinResponse, OverallCaptionData, OverallChartData, UserResponseDistribution

router = APIRouter()

@router.get("/", response_model=ChartResponseV2)
async def get_chart_list(db: AsyncSession = Depends(get_db), page: int = Header(1), category: str | None = Header(None), search: str | None = Query(None)):
    """차트 데이터 목록 조회 API"""
    page_size = 4
    chart_data = await crud.get_chart_data_by_caption(db, page=page, page_size=page_size, category=category, search=search)
    return chart_data

@router.get("/all", response_model=OverallWassersteinResponse)
async def get_overall_wasserstein_distances(db: AsyncSession = Depends(get_db)):
    """전체 캡션의 wasserstein distance 평균을 flag별로 조회하는 API"""
    overall_data = await crud.get_overall_wasserstein_distances(db)

    # Convert the result to the expected schema format (same as single caption API)
    cultural_distances = []
    visual_distances = []
    hallucination_distances = []

    # Sort flags and create lists of distances by flag order
    for flag in sorted(overall_data.keys()):
        distances = overall_data[flag]
        cultural_distances.append(distances["cultural"])
        visual_distances.append(distances["visual"])
        hallucination_distances.append(distances["hallucination"])

    # Create dummy user response distribution (all zeros since this is aggregate data)
    dummy_user_distribution = UserResponseDistribution(
        cultural=[0.0] * 5,
        visual=[0.0] * 5,
        hallucination=[0.0] * 5
    )

    chart_data = OverallChartData(
        cultural=cultural_distances,
        visual=visual_distances,
        hallucination=hallucination_distances
    )

    response_data = OverallCaptionData(
        chartdata=chart_data,
        userResponseDistribution=dummy_user_distribution
    )

    return OverallWassersteinResponse(responseData=response_data)

@router.get("/{caption_id}", response_model=SingleChartResponse)
async def get_single_chart(caption_id: int, db: AsyncSession = Depends(get_db)):
    """단일 캡션에 대한 차트 데이터 조회 API"""
    caption_data = await crud.get_chart_data_for_single_caption(db, caption_id=caption_id)
    if not caption_data:
        raise HTTPException(status_code=404, detail="Caption not found")

    return SingleChartResponse(responseData=caption_data)

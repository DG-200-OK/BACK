import json
import random
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Header, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.survey import Survey, SurveyCreate, UploadImageResponseData, SurveyInfo, SurveyResponse, OnGoingListResponse, OnGoingSurvey
from schemas.chart import ChartResponseV2
from schemas.response import Response, ResponseCreate
from schemas.base import GenericResponse
import crud
from database import get_db
# from utils.s3 import upload_to_s3 # S3 기능 비활성화

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_survey(
    db: AsyncSession = Depends(get_db),
    user_id: int = Header(..., alias="user-id"),
    country: str = Form(...),
    category: str = Form(...),
    title: str = Form(...),
    imageFile: UploadFile = File(...),
    level1: Optional[str] = Form(None),
    level2: Optional[str] = Form(None),
    level3: Optional[str] = Form(None),
    level4: Optional[str] = Form(None),
):
    """설문 등록 API"""
    if not imageFile.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미지 파일이 첨부되지 않았습니다.")

    # image_url = upload_to_s3(imageFile) # S3 기능 비활성화
    image_url = "s3_disabled_placeholder.jpg" # 임시 이미지 URL
    category_map = {
        "architecture": "Architecture",
        "clothes": "Clothing",
        "cuisine": "Cuisine",
        "game": "Game",
        "tool": "Tool"
    }
    country_map = {
        "Korea": "한국",
        "Japan": "일본",
        "China": "중국"
    }
    category = category_map.get(category, category)
    country = country_map.get(country, country)

    survey_in = SurveyCreate(
        title=title,
        country=country,
        category=category,
        imageUrl=image_url,
        userId=user_id,
        level1=level1,
        level2=level2,
        level3=level3,
        level4=level4,
    )
    await crud.create_survey(db=db, survey=survey_in)
    return JSONResponse(content={"success": True, "responseData": {}})

@router.get("/register", response_model=ChartResponseV2)
async def get_registered_surveys(
    user_id: int = Header(..., alias="user-id"),
    db: AsyncSession = Depends(get_db),
    page: int = Header(1),
    category: Optional[str] = Header(None), # <--- 수정
    search: Optional[str] = Query(None)      # <--- 수정
):
    """사용자가 등록한 설문 목록 조회 API"""
    page_size = 4
    chart_data = await crud.get_chart_data_by_caption(db, page=page, page_size=page_size, category=category, search=search, user_id=user_id)
    return chart_data

@router.post("/test", response_model=UploadImageResponseData)
async def test_image_upload(image: UploadFile = File(...)):
    """이미지 업로드 테스트 API"""
    if not image.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미지 파일이 첨부되지 않았습니다.")

    # image_url = upload_to_s3(image) # S3 기능 비활성화
    image_url = "s3_disabled_placeholder.jpg" # 임시 이미지 URL
    return {"imageUrl": image_url}


@router.get("/", response_model=SurveyResponse, response_model_by_alias=False)
async def get_all_surveys(
    db: AsyncSession = Depends(get_db), 
    user_id: int = Header(..., alias="user-id"),
    page: int = Header(1),
    category: Optional[str] = Query(None), # <--- 수정
    search: Optional[str] = Query(None)    # <--- 수정
):
    """전체 설문 목록 조회 API"""
    surveys = await crud.get_surveys_with_progress(db, user_id=user_id, category=category, search=search)

    uncompleted_surveys = [survey for survey in surveys if survey.progress < 1.0]

    random.shuffle(uncompleted_surveys)
    uncompleted_surveys.sort(key=lambda s: s.total_responses)

    page_size = 4
    total_surveys = len(uncompleted_surveys)
    total_pages = math.ceil(total_surveys / page_size)

    start = (page - 1) * page_size
    end = start + page_size
    paginated_surveys = uncompleted_surveys[start:end]

    return {"totalPages": total_pages, "surveys": paginated_surveys}

@router.get("/ongoing", response_model=OnGoingListResponse)
async def get_ongoing_surveys(
    user_id: int = Header(..., alias="user-id"),
    db: AsyncSession = Depends(get_db)
):
    """진행 중인 설문 목록 조회 API"""
    surveys = await crud.get_ongoing_surveys(db, user_id=user_id)
    ongoing_list = [OnGoingSurvey.from_orm(survey) for survey in surveys]
    return {
        "success": True,
        "responseData": {"onGoingList": ongoing_list},
        "message": "요청에 성공했습니다."
    }

@router.get("/{id}", response_model=Survey)
async def get_survey_by_id(id: int, db: AsyncSession = Depends(get_db)):
    """ID로 특정 설문 조회 API"""
    survey = await crud.get_survey(db, survey_id=id)
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="설문을 찾을 수 없습니다.")
    return survey

@router.post("/response", status_code=status.HTTP_201_CREATED, response_model=Response, response_model_by_alias=False)
async def create_survey_response(
    response_in: ResponseCreate,
    db: AsyncSession = Depends(get_db)
):
    """설문 응답 생성 API"""
    new_response = await crud.create_response(db=db, response=response_in)
    return new_response

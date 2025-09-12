import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Header
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.survey import Survey, SurveyCreate, UploadImageResponseData
from schemas.response import Response, ResponseCreate
import crud
from database import get_db
from utils.s3 import upload_to_s3

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Survey)
async def create_survey(
    db: AsyncSession = Depends(get_db),
    country: str = Form(...),
    category: str = Form(...),
    entityName: str = Form(...),
    captions: str = Form(...),  # 프론트엔드에서 JSON 문자열로 보냄
    image: UploadFile = File(...)
):
    """설문 생성 API"""
    if not image.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미지 파일이 첨부되지 않았습니다.")

    image_url = upload_to_s3(image)
    
    try:
        captions_list = json.loads(captions)
        if not isinstance(captions_list, list):
            raise ValueError()
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Captions는 반드시 리스트 형태의 JSON 문자열이어야 합니다.")

    survey_in = SurveyCreate(
        title=entityName,
        country=country,
        category=category,
        imageUrl=image_url,
        captions=captions_list,
    )
    new_survey = await crud.create_survey(db=db, survey=survey_in)
    return new_survey

@router.post("/test", response_model=UploadImageResponseData)
async def test_image_upload(image: UploadFile = File(...)):
    """이미지 업로드 테스트 API"""
    if not image.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미지 파일이 첨부되지 않았습니다.")
    
    image_url = upload_to_s3(image)
    return {"imageUrl": image_url}


@router.get("/", response_model=List[Survey], response_model_by_alias=False)
async def get_all_surveys(
    db: AsyncSession = Depends(get_db), 
    user_id: int = Header(..., alias="user-id"),
    page: int = Header(1, alias="page")
):
    """전체 설문 목록 조회 API"""
    limit = 5
    skip = (page - 1) * limit
    surveys = await crud.get_surveys_with_progress(db, user_id=user_id, skip=skip, limit=limit)
    return surveys

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
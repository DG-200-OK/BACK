from fastapi import APIRouter
from .. import crud
from ..schemas import data as data_schema

router = APIRouter(
    prefix="/data",
    tags=["data"]
)

# API 4: 데이터 검색 요청
@router.post("/search", response_model=data_schema.DataSearchResponse)
def request_data_search(request: data_schema.DataSearchRequest):
    return crud.create_dummy_data_search(request=request)
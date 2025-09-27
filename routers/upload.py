from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import crud
from database import get_db, AsyncSessionLocal
import requests
import tempfile
from fastapi import UploadFile
from utils.s3 import upload_local_file_to_s3
import os
from fastapi.concurrency import run_in_threadpool

router = APIRouter()

def download_and_save_image(url: str) -> tuple[str, str, str]:
    response = requests.get(url, stream=True)
    response.raise_for_status()
    content_type = response.headers.get('content-type')
    filename = url.split("/")[-1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        for chunk in response.iter_content(chunk_size=8192):
            tmp_file.write(chunk)
        tmp_file_path = tmp_file.name
    return tmp_file_path, filename, content_type

@router.post("/start")
async def start_upload():
    """외부 이미지 URL을 S3로 업로드하고 데이터베이스를 업데이트합니다."""
    async with AsyncSessionLocal() as db:
        surveys = await crud.get_all_surveys_for_upload(db)
    
    upload_tasks = []
    for survey in surveys:
        if "culturelens" not in survey.imageUrl:
            upload_tasks.append(survey)

    for survey in upload_tasks:
        try:
            tmp_file_path, filename, content_type = await run_in_threadpool(download_and_save_image, survey.imageUrl)
            
            new_image_url = await run_in_threadpool(upload_local_file_to_s3, tmp_file_path, filename, content_type)
            
            async with AsyncSessionLocal() as update_db:
                await crud.update_survey_image_url(update_db, survey.surveyId, new_image_url)

            os.unlink(tmp_file_path)

        except Exception as e:
            print(f"An error occurred while processing survey {survey.surveyId}: {e}")

    return {"message": "Upload process started."}

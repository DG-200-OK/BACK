import boto3
import uuid
from fastapi import UploadFile
from config import settings

s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_s3_region_name,
)

def upload_to_s3(file: UploadFile) -> str:
    """AWS S3에 파일을 업로드하고 파일 URL을 반환합니다."""
    filename = f"{uuid.uuid4()}-{file.filename}"
    s3_key = f"upload/survey/{filename}"
    
    s3.upload_fileobj(
        file.file,
        settings.aws_s3_bucket_name,
        s3_key,
        ExtraArgs={"ACL": "public-read", "ContentType": file.content_type},
    )

    # return f"https://{settings.aws_s3_bucket_name}.s3.{settings.aws_s3_region_name}.amazonaws.com/upload/survey/{filename}"
    return f"https://culturelens.cloud/upload/survey/{filename}"

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

def upload_to_s3(file: UploadFile, content_type: str = None) -> str:
    """AWS S3에 파일을 업로드하고 파일 URL을 반환합니다."""
    filename = f"{uuid.uuid4()}-{file.filename}"
    s3_key = f"upload/survey/{filename}"
    
    s3.upload_fileobj(
        file.file,
        settings.aws_s3_bucket_name,
        s3_key,
        ExtraArgs={"ACL": "public-read", "ContentType": content_type or file.content_type},
    )

    # return f"https://{settings.aws_s3_bucket_name}.s3.{settings.aws_s3_region_name}.amazonaws.com/upload/survey/{filename}"
    return f"https://culturelens.cloud/upload/survey/{filename}"

def upload_local_file_to_s3(file_path: str, filename: str, content_type: str = None) -> str:
    """로컬 파일을 S3에 업로드하고 파일 URL을 반환합니다."""
    with open(file_path, "rb") as f:
        s3_filename = f"{uuid.uuid4()}-{filename}"
        s3_key = f"upload/survey/{s3_filename}"
        
        s3.upload_fileobj(
            f,
            settings.aws_s3_bucket_name,
            s3_key,
            ExtraArgs={"ACL": "public-read", "ContentType": content_type},
        )
        return f"https://culturelens.cloud/upload/survey/{s3_filename}"

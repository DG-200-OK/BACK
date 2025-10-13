from pydantic_settings import BaseSettings
from urllib.parse import quote_plus

class Settings(BaseSettings):
    db_user: str = "admin"
    db_password: str
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "culture_db"

    jwt_secret_key: str
    jwt_algorithm: str
    
    # 아래 AWS 관련 설정은 S3 비활성화를 위해 모두 주석 처리합니다.
    # aws_access_key_id: str
    # aws_secret_access_key: str
    # aws_s3_bucket_name: str
    port: int = 8000

    class Config:
        env_file = ".env"

    @property
    def database_url(self) -> str:
        # URL-encode the password to handle special characters
        encoded_password = quote_plus(self.db_password)
        return f"mysql+aiomysql://{self.db_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}"

settings = Settings()

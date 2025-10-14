from pydantic_settings import BaseSettings
from urllib.parse import quote_plus

class Settings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_s3_region_name: str
    aws_s3_bucket_name: str
    port: int = 8000

    class Config:
        env_file = ".env"

    @property
    def database_url(self) -> str:
        # URL-encode the password to handle special characters
        encoded_password = quote_plus(self.db_password)
        return f"mysql+aiomysql://{self.db_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}"

settings = Settings()

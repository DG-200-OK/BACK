from pydantic import BaseModel, Field
from typing import List, Optional # <--- Optional 추가
from schemas.survey import SurveyInfo

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    gender: str
    email: str

class UserUpdate(BaseModel):
    username: Optional[str] = None # <--- 수정
    password: Optional[str] = None # <--- 수정

class UserInDB(UserBase):
    userId: int
    class Config:
        from_attributes = True
        # V2 Pydantic에서는 아래와 같이 변경되었습니다.
        # allow_population_by_field_name = True
        validate_by_name = True


class LoginResponseData(BaseModel):
    userId: int
    username: str

class MyPageData(BaseModel):
    username: str
    email: str
    participatedSurvey: List[SurveyInfo]
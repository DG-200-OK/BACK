from pydantic import BaseModel, Field

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None


class UserInDB(UserBase):
    userId: int 
    class Config:
        from_attributes = True
        allow_population_by_field_name = True

class LoginResponseData(BaseModel):
    userId: int
    username: str

from typing import List

class MyPageResponse(BaseModel):
    surveyId: int
    choice: int

class MyPageData(BaseModel):
    username: str
    responses: List[MyPageResponse]

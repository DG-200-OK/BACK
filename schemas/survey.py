from pydantic import BaseModel, Field
from typing import List, Optional

# Caption Schemas
class CaptionBase(BaseModel):
    text: str
    type: Optional[str] = None

class CaptionCreate(CaptionBase):
    pass

class Caption(CaptionBase):
    captionId: int
    surveyId: int
    class Config:
        from_attributes = True
        allow_population_by_field_name = True

# Survey Schemas
class SurveyBase(BaseModel):
    imageUrl: str 
    country: str
    category: str
    title: str

class SurveyCreate(SurveyBase):
    userId: int
    level1: Optional[str] = None
    level2: Optional[str] = None
    level3: Optional[str] = None
    level4: Optional[str] = None

class Survey(SurveyBase):
    surveyId: int
    captions: List[Caption] = []
    progress: Optional[float] = None
    class Config:
        from_attributes = True
        allow_population_by_field_name = True

class SurveyResponse(BaseModel):
    totalPages: int
    surveys: List[Survey]

class UploadImageResponseData(BaseModel):
    imageUrl: str

class SurveyInfo(BaseModel):
    title: str
    category: str
    country: str
    imageUrl: str
    class Config:
        from_attributes = True

class RegisterSurveyData(BaseModel):
    registerSurvey: List[SurveyInfo]

class OnGoingSurvey(BaseModel):
    surveyId: int
    title: str
    category: str
    country: str
    imageUrl: str
    progress: float
    captions: List[Caption] = []

    class Config:
        from_attributes = True

class OnGoingListResponse(BaseModel):
    success: bool
    responseData: dict[str, list[OnGoingSurvey]]
    message: str

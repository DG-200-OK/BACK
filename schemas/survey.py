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
    captions: List[CaptionCreate]

class Survey(SurveyBase):
    surveyId: int
    captions: List[Caption] = []
    progress: Optional[float] = None
    class Config:
        from_attributes = True
        allow_population_by_field_name = True

class UploadImageResponseData(BaseModel):
    imageUrl: str

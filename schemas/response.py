from pydantic import BaseModel, Field

class ResponseBase(BaseModel):
    cultural: int = 0
    visual: int = 0
    hallucination: int = 0

class ResponseCreate(ResponseBase):
    userId: int = 0
    captionId: int = 0
    responseTime: float = 0.0
    class Config:
        allow_population_by_field_name = True
        populate_by_name = True

class Response(ResponseBase):
    responseId: int 
    userId: int 
    captionId: int 
    time: float 
    class Config:
        from_attributes = True
        allow_population_by_field_name = True

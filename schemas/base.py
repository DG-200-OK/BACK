from pydantic import BaseModel
from typing import Optional, TypeVar, Generic

T = TypeVar('T')

class GenericResponse(BaseModel, Generic[T]):
    success: bool = True
    responseData: Optional[T] = None
    statusCode: int = 200
    message: str = "요청에 성공하였습니다."
    class Config:
        from_attributes = True
        allow_population_by_field_name = True

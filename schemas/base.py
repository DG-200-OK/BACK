from pydantic import BaseModel
from typing import Optional, TypeVar, Generic

T = TypeVar('T')

class GenericResponse(BaseModel, Generic[T]):
    status: str = "success"
    responseData: Optional[T] = None
    class Config:
        from_attributes = True
        allow_population_by_field_name = True

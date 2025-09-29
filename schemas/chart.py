from pydantic import BaseModel
from typing import List, Dict

class ChartDataValues(BaseModel):
    people: List[float]
    agent: List[float]

class ChartData(BaseModel):
    cultural: ChartDataValues
    visual: ChartDataValues
    hallucination: ChartDataValues

class CaptionChartData(BaseModel):
    captionId: int
    title: str
    imageUrl: str
    content: str
    chartdata: ChartData

class ChartResponseV2(BaseModel):
    responseData: List[CaptionChartData]
    totalPage: int
    success: bool = True
    message: str = "요청에 성공하였습니다."

# New schema for the chartdata in the single caption response
class NewChartData(BaseModel):
    cultural: List[float | None]
    visual: List[float | None]
    hallucination: List[float | None]

# New schema for the user distribution
class UserResponseDistribution(BaseModel):
    cultural: List[float]
    visual: List[float]
    hallucination: List[float]

class NewCaptionChartData(BaseModel):
    captionId: int
    title: str
    imageUrl: str
    content: str
    chartdata: NewChartData
    userResponseDistribution: UserResponseDistribution

class SingleChartResponse(BaseModel):
    responseData: NewCaptionChartData
    success: bool = True
    message: str = "요청에 성공하였습니다."

# Schema for overall wasserstein distance response (same format as single caption)
class OverallChartData(BaseModel):
    cultural: List[float | None]
    visual: List[float | None]
    hallucination: List[float | None]

class OverallCaptionData(BaseModel):
    captionId: int = 0  # Using 0 for overall data
    title: str = "Overall Distribution Analysis"
    imageUrl: str = ""
    content: str = "Average Wasserstein distances across all captions by flag"
    chartdata: OverallChartData
    userResponseDistribution: UserResponseDistribution

class OverallWassersteinResponse(BaseModel):
    responseData: OverallCaptionData
    success: bool = True
    message: str = "요청에 성공하였습니다."

from sqlalchemy import Column, BigInteger, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Survey(Base):
    __tablename__ = "survey"
    surveyId = Column(BigInteger, primary_key=True, autoincrement=True)
    imageUrl = Column(String(255))
    country = Column(String(255))
    category = Column(String(255))
    title = Column(String(255))
    captions = relationship("Caption", back_populates="survey")

class Caption(Base):
    __tablename__ = "caption"
    captionId = Column(BigInteger, primary_key=True, autoincrement=True)
    surveyId = Column(BigInteger, ForeignKey("survey.surveyId"))
    text = Column(String(255))
    type = Column(String(255))
    survey = relationship("Survey", back_populates="captions")
    responses = relationship("Response", back_populates="caption")

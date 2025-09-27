from sqlalchemy import Column, BigInteger, String, ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Response(Base):
    __tablename__ = "response"
    responseId = Column(BigInteger, primary_key=True, autoincrement=True)
    cultural = Column(Integer)
    visual = Column(Integer)
    hallucination = Column(Integer)
    time = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    userId = Column(BigInteger, ForeignKey("user.userId"))
    captionId = Column(BigInteger, ForeignKey("caption.captionId"))
    user = relationship("User", back_populates="responses")
    caption = relationship("Caption", back_populates="responses")

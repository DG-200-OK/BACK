from sqlalchemy import Column, BigInteger, String
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "user"
    userId = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    responses = relationship("Response", back_populates="user")

from sqlalchemy import Column, BigInteger, String, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from database import Base


class AgentEvalDetail(Base):
    __tablename__ = "agentEvalDetail"

    id = Column(Integer, primary_key=True, autoincrement=True, comment='Primary Key')
    type = Column(String(255), nullable=False, comment='ID of the source caption')
    likert = Column(Integer, nullable=False)
    value = Column(Float, nullable=False)
    flag = Column(Integer, nullable=False)
    captionId = Column(BigInteger, ForeignKey("caption.captionId"), nullable=False)

    caption = relationship("Caption", back_populates="agent_eval_details")

class AgentEvalDetailV2(Base):
    __tablename__ = "agentEvalDetail_v2"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    type = Column(String(255), nullable=False, comment='Type of evaluation (cultural, visual, hallucination)')
    likert = Column(Integer, nullable=False, comment='Likert scale value (1-5)')
    value = Column(Float, nullable=False, comment='Numeric value from distribution')
    flag = Column(Integer, nullable=False, comment='Flag value from API request')
    captionId = Column(BigInteger, ForeignKey("caption.captionId"), nullable=False)

    caption = relationship("Caption", back_populates="agent_eval_details_v2")

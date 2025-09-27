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

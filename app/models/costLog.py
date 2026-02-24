from app.models.uuid import uuid_pk

from sqlalchemy import Column , String ,Integer, Numeric, ForeignKey, Text, Boolean, DateTime

from sqlalchemy.orm import relationship

from .base import Base

from datetime import datetime

class CostLog(Base):
    __tablename__ = "cost_log"

    log_id = uuid_pk()
    
    run_id = Column(String, ForeignKey("runs.run_id"), unique=True)

    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    model_name = Column(String)
    cost_usd = Column(Numeric(10, 6)) 

    created_at = Column(DateTime, default=datetime.utcnow)

    # Runs
    run = relationship("Runs", back_populates="cost_details")
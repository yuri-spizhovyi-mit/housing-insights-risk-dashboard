from sqlalchemy import Column, String, Date, Numeric, TIMESTAMP, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from services.fapi.db import Base

class AnomalySignal(Base):
    __tablename__ = "anomaly_signals"

    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city = Column(String, nullable=False)
    target = Column(String, nullable=False)   # "price" or "rent"
    detect_date = Column(Date, nullable=False)
    anomaly_score = Column(Numeric(14, 4))
    is_anomaly = Column(Boolean, default=False)
    model_name = Column(String)
    created_at = Column(TIMESTAMP, server_default=text("now()"))

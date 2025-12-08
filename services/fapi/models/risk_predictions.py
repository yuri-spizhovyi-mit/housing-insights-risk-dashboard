from sqlalchemy import Column, String, Date, Numeric, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from services.fapi.db import Base


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city = Column(String, nullable=False)
    risk_type = Column(String, nullable=False)  # affordability, volatility, etc.
    predict_date = Column(Date, nullable=False)
    risk_value = Column(Numeric(14, 4), nullable=False)
    model_name = Column(String)
    created_at = Column(TIMESTAMP, server_default=text("now()"))

# services/fapi/models/model_comparison.py
from sqlalchemy import Column, String, Integer, Numeric, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from fapi.db import Base
import uuid

class ModelComparison(Base):
    __tablename__ = "model_comparison"

    city = Column(String, primary_key=True)
    target = Column(String, primary_key=True)
    horizon_months = Column(Integer, primary_key=True)
    model_name = Column(String, primary_key=True)

    mae = Column(Numeric(14, 4))
    mape = Column(Numeric(14, 4))
    rmse = Column(Numeric(14, 4))
    mse = Column(Numeric(14, 4))
    r2 = Column(Numeric(14, 4))

    evaluated_at = Column(TIMESTAMP, server_default=func.now())

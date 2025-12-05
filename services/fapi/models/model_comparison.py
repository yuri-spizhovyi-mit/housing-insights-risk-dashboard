# services/fapi/models/model_comparison.py
from sqlalchemy import Column, String, Integer, Float, TIMESTAMP
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

    mae = Column(Float)
    mape = Column(Float)
    rmse = Column(Float)
    mse = Column(Float)
    r2 = Column(Float)

    evaluated_at = Column(TIMESTAMP, server_default=func.now())

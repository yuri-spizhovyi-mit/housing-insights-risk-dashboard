from sqlalchemy import Column, String, Integer, Date, Numeric, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..db import Base
import uuid


class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    model_name = Column(String, nullable=False)
    target = Column(String, nullable=False)  # "price" or "rent"
    horizon_months = Column(Integer, nullable=False)  # 12, 24, 60, 120
    city = Column(String, nullable=False)

    property_type = Column(String)
    beds = Column(Integer)
    baths = Column(Integer)
    sqft_min = Column(Integer)
    sqft_max = Column(Integer)
    year_built_min = Column(Integer)
    year_built_max = Column(Integer)

    predict_date = Column(Date, nullable=False)

    yhat = Column(Numeric(14, 4), nullable=False)
    yhat_lower = Column(Numeric(14, 4))
    yhat_upper = Column(Numeric(14, 4))

    features_version = Column(Text, default="feat-v1")
    model_artifact_uri = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from services.fastapi.models.model_predictions import ModelPrediction

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("")
def list_cities(db: Session = Depends(get_db)):
    rows = (
        db.query(ModelPrediction.city).distinct().order_by(ModelPrediction.city).all()
    )
    return {"cities": [r[0] for r in rows]}

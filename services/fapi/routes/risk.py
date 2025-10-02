from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.fapi.db import get_db
from services.fapi.models.risk_predictions import RiskPrediction

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("")
def get_risk(city: str, db: Session = Depends(get_db)):
    rows = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.city == city)
        .order_by(RiskPrediction.predict_date.desc())
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No risk data for {city}")

    return {
        "city": city,
        "latest_date": rows[0].predict_date.isoformat(),
        "indices": [{"type": r.risk_type, "value": float(r.risk_value)} for r in rows],
    }

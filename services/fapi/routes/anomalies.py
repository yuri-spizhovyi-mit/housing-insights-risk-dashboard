from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.fapi.db import get_db
from services.fapi.models.anomaly_signals import AnomalySignal

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("")
def get_anomalies(city: str, target: str, db: Session = Depends(get_db)):
    rows = (
        db.query(AnomalySignal)
        .filter(AnomalySignal.city == city, AnomalySignal.target == target)
        .order_by(AnomalySignal.detect_date)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No anomalies for {city}/{target}")

    return {
        "city": city,
        "target": target,
        "signals": [
            {
                "date": r.detect_date.isoformat(),
                "score": float(r.anomaly_score),
                "is_anomaly": r.is_anomaly,
            }
            for r in rows
        ],
    }

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

    # Extract latest snapshot by type
    indices = {r.risk_type: float(r.risk_value) for r in rows}

    # Map to old format
    return {
        "city": city,
        "date": rows[0].predict_date.isoformat(),
        "score": round(indices.get("composite_index", 0) * 100),  # 0–1 -> %
        "breakdown": [
            {"name": "Affordability", "status": "Tight" if indices.get("affordability", 0) > 0.7 else "OK"},
            {"name": "Price-to-Rent", "status": "Elevated" if indices.get("price_to_rent", 0) > 0.6 else "Normal"},
            {"name": "Inventory", "status": "Low" if indices.get("inventory", 0) < 0.5 else "Adequate"},
        ],
    }

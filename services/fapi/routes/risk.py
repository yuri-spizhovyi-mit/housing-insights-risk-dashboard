from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.fapi.db import get_db
from services.fapi.models.risk_predictions import RiskPrediction

router = APIRouter(prefix="/risk", tags=["risk"])


def map_affordability(v: float) -> str:
    if v >= 0.8:
        return "Tight"
    elif v >= 0.5:
        return "Moderate"
    return "Comfortable"


def map_price_to_rent(v: float) -> str:
    if v >= 0.7:
        return "Elevated"
    elif v >= 0.4:
        return "Balanced"
    return "Attractive"


def map_inventory(v: float) -> str:
    if v < 0.4:
        return "Low"
    elif v < 0.7:
        return "Adequate"
    return "High"


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

    indices = {r.risk_type: float(r.risk_value) for r in rows}

    return {
        "city": city,
        "date": rows[0].predict_date.isoformat(),
        "score": round(indices.get("composite_index", 0) * 100),
        "breakdown": [
            {
                "name": "Affordability",
                "status": map_affordability(indices.get("affordability", 0)),
            },
            {
                "name": "Price-to-Rent",
                "status": map_price_to_rent(indices.get("price_to_rent", 0)),
            },
            {"name": "Inventory", "status": map_inventory(indices.get("inventory", 0))},
        ],
    }

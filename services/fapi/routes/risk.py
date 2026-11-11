from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models.risk_predictions import RiskPrediction

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
    city = city.strip().title()
    rows = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.city == city)
        .order_by(RiskPrediction.predict_date.desc())
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No risk data for {city}")

    latest = rows[0].predict_date
    indices = {r.risk_type: float(r.risk_value) for r in rows if r.predict_date == latest}

    return {
        "city": city,
        "date": rows[0].predict_date.isoformat(),
        "score": round(indices["composite_index"] * 100) if "composite_index" in indices else None,
        "breakdown": [
            {
                "name": "Affordability",
                "status": map_affordability(indices["affordability"]) if "affordability" in indices else "Unavailable",
            },
            {
                "name": "Price-to-Rent",
                "status": map_price_to_rent(indices["price_to_rent"]) if "price_to_rent" in indices else "Unavailable",
            },
            {"name": "Inventory", "status": map_inventory(indices["inventory"]) if "inventory" in indices else "Unavailable"},
        ],
    }

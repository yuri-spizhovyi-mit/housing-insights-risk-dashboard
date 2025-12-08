from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from services.fapi.db import get_db
from services.fapi.models.model_predictions import ModelPrediction

router = APIRouter(prefix="/forecast", tags=["forecast"])

HORIZON_MAP = {"1y": 12, "2y": 24, "5y": 60, "10y": 120}


@router.get("")
def get_forecast(
    city: str,
    target: str = Query("price", enum=["price", "rent"]),
    horizon: str = Query("1y", enum=list(HORIZON_MAP.keys())),
    model: str = Query("arima"),
    propertyType: str | None = None,
    beds: int | None = Query(-1),
    baths: int | None = Query(-1),
    db: Session = Depends(get_db),
):
    months = HORIZON_MAP[horizon]

    # Load full monthly series (1..months)
    rows = (
        db.query(ModelPrediction)
        .filter(
            ModelPrediction.city == city,
            ModelPrediction.target == target,
            ModelPrediction.model_name == model,  # ⭐ important
            ModelPrediction.horizon_months.between(1, months),  # ⭐ only this
        )
        .order_by(ModelPrediction.predict_date)
        .all()
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No data for {city}, {target}, {horizon}, model={model}",
        )

    # Convert to API format
    full = [
        {
            "date": r.predict_date.isoformat(),
            "value": float(r.yhat),
            "lower": float(r.yhat_lower) if r.yhat_lower else None,
            "upper": float(r.yhat_upper) if r.yhat_upper else None,
        }
        for r in rows
    ]

    # Sampling logic
    if months == 12:
        sampled = full
    elif months == 24:
        sampled = full[::2]  # 12 points
    elif months >= 60:
        step = max(1, len(full) // 12)
        sampled = full[::step][:12]
    else:
        sampled = full

    return {
        "city": city,
        "target": target,
        "horizon": months,
        "model": model,
        "data": sampled,
    }

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from fapi.db import get_db
from fapi.models.model_predictions import ModelPrediction
from datetime import date, timedelta

router = APIRouter(prefix="/forecast", tags=["forecast"])

HORIZON_MAP = {"1y": 12, "2y": 24, "5y": 60, "10y": 120}


@router.get("")
def get_forecast(
    city: str,
    target: str = Query("price", enum=["price", "rent"]),
    horizon: str = Query("1y", enum=list(HORIZON_MAP.keys())),
    model: str = Query("arima"),   # ⭐ NEW: allow selecting model directly
    propertyType: str | None = None,
    beds: int | None = Query(-1),
    baths: int | None = Query(-1),
    db: Session = Depends(get_db),
):
    months = HORIZON_MAP[horizon]

    # Load all rows for this horizon
    rows = (
        db.query(ModelPrediction)
        .filter(
            ModelPrediction.city == city,
            ModelPrediction.target == target,
            ModelPrediction.horizon_months == months,
            ModelPrediction.model_name == model,
        )
        .order_by(ModelPrediction.predict_date)
        .all()
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No data for {city}, {target}, {horizon}, model={model}",
        )

    # Build full list
    full = [
        {
            "date": r.predict_date.isoformat(),
            "value": float(r.yhat),
            "lower": float(r.yhat_lower) if r.yhat_lower else None,
            "upper": float(r.yhat_upper) if r.yhat_upper else None,
        }
        for r in rows
    ]

    # ⭐ Sampling logic
    if months == 12:
        # 1 year: return monthly (12 points)
        sampled = full
    elif months == 24:
        # 2 years: every second month → select indexes 0, 2, 4...
        sampled = full[::2]
    elif months >= 60:
        # 5 years or 10 years: return 12 evenly spaced points
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

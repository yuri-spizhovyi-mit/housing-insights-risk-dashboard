from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from services.fapi.db import get_db  # ✅
from services.fapi.models.model_predictions import ModelPrediction  # ✅
from datetime import date, timedelta

router = APIRouter(prefix="/forecast", tags=["forecast"])

HORIZON_MAP = {"1y": 12, "2y": 24, "5y": 60, "10y": 120}


@router.get("")
def get_forecast(
    city: str,
    horizon: str = Query("1y", enum=list(HORIZON_MAP.keys())),
    propertyType: str | None = None,
    beds: int | None = None,
    baths: int | None = None,
    sqftMin: int | None = None,
    sqftMax: int | None = None,
    yearBuiltMin: int | None = None,
    yearBuiltMax: int | None = None,
    db: Session = Depends(get_db),
):
    months = HORIZON_MAP[horizon]
    start_date = date.today()
    end_date = start_date + timedelta(days=30 * months)

    query = db.query(ModelPrediction).filter(
        ModelPrediction.city == city,
        ModelPrediction.predict_date >= start_date,
        ModelPrediction.predict_date <= end_date,
    )

    if propertyType:
        query = query.filter(ModelPrediction.property_type == propertyType)
    if beds:
        query = query.filter(ModelPrediction.beds == beds)
    if baths:
        query = query.filter(ModelPrediction.baths == baths)
    if sqftMin:
        query = query.filter(ModelPrediction.sqft_min >= sqftMin)
    if sqftMax:
        query = query.filter(ModelPrediction.sqft_max <= sqftMax)
    if yearBuiltMin:
        query = query.filter(ModelPrediction.year_built_min >= yearBuiltMin)
    if yearBuiltMax:
        query = query.filter(ModelPrediction.year_built_max <= yearBuiltMax)

    rows = query.order_by(ModelPrediction.predict_date).all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No forecast data for {city}")

    return {
        "city": city,
        "target": "price",  # or "rent", from row.target
        "horizon": months,
        "data": [
            {
                "date": row.predict_date.isoformat(),
                "value": float(row.yhat),
                "lower": float(row.yhat_lower) if row.yhat_lower else None,
                "upper": float(row.yhat_upper) if row.yhat_upper else None,
            }
            for row in rows
        ],
    }

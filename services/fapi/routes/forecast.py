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
    propertyType: str | None = None,
    beds: int | None = Query(-1, description="Number of beds, -1 = Any"),
    baths: int | None = Query(-1, description="Number of baths, -1 = Any"),
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
        ModelPrediction.target == target,
        ModelPrediction.horizon_months == months,
        ModelPrediction.predict_date >= start_date,
        ModelPrediction.predict_date <= end_date,
    )

    if propertyType:
        query = query.filter(ModelPrediction.property_type == propertyType)

    # Beds filter (default Any -> NULL)
    if beds == -1:
        query = query.filter(ModelPrediction.beds.is_(None))
    else:
        query = query.filter(ModelPrediction.beds == beds)

    # Baths filter (default Any -> NULL)
    if baths == -1:
        query = query.filter(ModelPrediction.baths.is_(None))
    else:
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

    # Return only one row per date (dedup safeguard)
    data_by_date = {}
    for row in rows:
        if row.predict_date not in data_by_date:
            data_by_date[row.predict_date] = {
                "date": row.predict_date.isoformat(),
                "value": float(row.yhat),
                "lower": float(row.yhat_lower) if row.yhat_lower is not None else None,
                "upper": float(row.yhat_upper) if row.yhat_upper is not None else None,
            }

    return {
        "city": city,
        "target": target,
        "horizon": months,
        "data": list(data_by_date.values()),
    }

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from services.fapi.db import get_db
from services.fapi.models.model_comparison import ModelComparison

router = APIRouter(prefix="/model-comparison", tags=["model-comparison"])


@router.get("")
def get_model_comparison(
    city: str,
    target: str = Query(..., enum=["price", "rent"]),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ModelComparison)
        .filter(ModelComparison.city == city, ModelComparison.target == target)
        .order_by(
            ModelComparison.horizon_months.asc(), ModelComparison.model_name.asc()
        )
        .all()
    )

    if not rows:
        raise HTTPException(
            status_code=404, detail=f"No comparison data for {city}/{target}"
        )

    response = {"city": city, "target": target, "horizons": [], "models": {}}

    for row in rows:
        h = int(row.horizon_months)
        m = row.model_name.replace("_backtest", "")

        if h not in response["horizons"]:
            response["horizons"].append(h)

        if m not in response["models"]:
            response["models"][m] = []

        response["models"][m].append(
            {
                "horizon": h,
                "mae": float(row.mae) if row.mae is not None else None,
                "mape": float(row.mape) if row.mape is not None else None,
                "rmse": float(row.rmse) if row.rmse is not None else None,
                "mse": float(row.mse) if row.mse is not None else None,
                "r2": float(row.r2) if row.r2 is not None else None,
            }
        )

    return response

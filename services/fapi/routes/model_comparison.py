from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from fapi.db import get_db

router = APIRouter(prefix="/model-comparison", tags=["model-comparison"])


@router.get("")
def get_model_comparison(
    city: str,
    target: str = Query(..., enum=["price", "rent"]),
    db: Session = Depends(get_db),
):
    """
    Returns comparison metrics for ARIMA, Prophet, and LSTM across horizons.
    """

    sql = text("""
        SELECT
            city,
            target,
            horizon_months,
            model_name,
            mae,
            mape,
            rmse,
            mse,
            r2
        FROM public.model_comparison
        WHERE city = :city
          AND target = :target
        ORDER BY horizon_months ASC, model_name ASC
    """)

    rows = db.execute(sql, {"city": city, "target": target}).mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No comparison data for city={city}, target={target}",
        )

    response = {
        "city": city,
        "target": target,
        "horizons": [],
        "models": {},
    }

    for row in rows:
        h = row["horizon_months"]
        m = row["model_name"].replace("_backtest", "")

        if h not in response["horizons"]:
            response["horizons"].append(h)

        if m not in response["models"]:
            response["models"][m] = []

        response["models"][m].append(
            {
                "horizon": h,
                "mae": row["mae"],
                "mape": row["mape"],
                "rmse": row["rmse"],
                "mse": row["mse"],
                "r2": row["r2"],
            }
        )

    return response

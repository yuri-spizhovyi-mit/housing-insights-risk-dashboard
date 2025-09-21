from fastapi import APIRouter, HTTPException
from db import query
import logging

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/{city}")
def get_forecast(city: str):
    try:
        sql = """
            SELECT 
                predict_date AS date,
                yhat AS p50,
                yhat_lower AS p80,
                yhat_upper AS p95
            FROM model_predictions
            WHERE city = %s
            ORDER BY predict_date
        """
        rows = query(sql, (city,))

        if not rows:
            raise HTTPException(
                status_code=404, detail=f"No forecast data found for {city}"
            )

        return rows

    except Exception:
        logging.exception("Database error in /forecast/%s", city)
        raise HTTPException(status_code=500, detail="Internal server error")

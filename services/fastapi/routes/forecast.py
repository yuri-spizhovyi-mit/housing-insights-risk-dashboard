from fastapi import APIRouter
from ..db import query

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/{city}")
def get_forecast(city: str):
    sql = """
        SELECT forecast_date, p50, p80, p95, risk_index
        FROM model_predictions
        WHERE city = %s
        ORDER BY forecast_date
    """
    return query(sql, (city,))

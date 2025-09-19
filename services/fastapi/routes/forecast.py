from fastapi import APIRouter
from services.fastapi.db import query

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
        return query(sql, (city,))
    except Exception as e:
        return {"error": str(e)}

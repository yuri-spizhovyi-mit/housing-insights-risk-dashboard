from fastapi import APIRouter
from db import query

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("")
def list_cities():
    try:
        sql = "SELECT DISTINCT city FROM model_predictions ORDER BY city"
        rows = query(sql)
        return {"cities": [r.get("city") for r in rows]}
    except Exception as e:
        return {"error": str(e)}

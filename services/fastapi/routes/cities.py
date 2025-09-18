from fastapi import APIRouter
from services.fastapi.db import query

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("")
def list_cities():
    sql = "SELECT DISTINCT city FROM model_predictions ORDER BY city"
    rows = query(sql)
    return {"cities": [r["city"] for r in rows]}

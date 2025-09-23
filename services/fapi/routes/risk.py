from fastapi import APIRouter
from datetime import date

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("")
def get_risk(city: str):
    # placeholder synthetic example
    return {
        "city": city,
        "date": date.today().isoformat(),
        "score": 62,
        "breakdown": [
            {"name": "Affordability", "status": "Tight"},
            {"name": "Price-to-Rent", "status": "Elevated"},
            {"name": "Inventory", "status": "Low"},
        ],
    }

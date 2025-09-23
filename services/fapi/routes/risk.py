from fastapi import APIRouter

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/{city}")
def get_risk(city: str):
    # placeholder synthetic example
    return {
        "city": "Toronto",
        "date": "2025-09-21",
        "score": 62,
        "breakdown": [
            {"name": "Affordability", "status": "Tight"},
            {"name": "Price-to-Rent", "status": "Elevated"},
            {"name": "Inventory", "status": "Low"},
        ],
    }

from fastapi import APIRouter

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/{city}")
def get_risk(city: str):
    # placeholder synthetic example
    return {
        "city": city,
        "risk_index": 0.45,
        "level": "Moderate",
        "indicators": {"affordability": 0.6, "price_to_rent": 28.5, "inventory": "Low"},
    }

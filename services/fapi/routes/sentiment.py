from fastapi import APIRouter

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/{city}")
def get_sentiment(city: str):
    # Placeholder synthetic sentiment for MVP
    return {
        "city": city,
        "sentiment_index": 0.42,
        "label": "Negative",
        "trend_30d": [0.55, 0.51, 0.47, 0.42],
        "top_headlines": [
            f"{city} rental demand rises",
            "Rate cuts delayed; affordability worsens",
            "New supply targets announced",
        ],
        "last_updated": "2025-09-25",
    }

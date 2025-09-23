from fastapi import APIRouter

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("")
def get_sentiment(city: str):
    # Placeholder synthetic response — later connect to news_sentiment table
    return {
        "city": city,
        "items": [
            {
                "date": "2025-08-29",
                "headline": "New supply targets announced",
                "sentiment": "NEU",
            },
            {
                "date": "2025-08-14",
                "headline": "Rate cuts delayed; affordability worsens",
                "sentiment": "NEG",
            },
            {
                "date": "2025-07-28",
                "headline": f"{city} rental demand rises",
                "sentiment": "POS",
            },
        ],
    }

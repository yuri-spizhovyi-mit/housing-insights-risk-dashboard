from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..db import get_db
from ..models.news import NewsArticle  # ✅ import here

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("")
def get_sentiment(city: str, db: Session = Depends(get_db)):
    rows = (
        db.query(NewsArticle)
        .filter(NewsArticle.city == city)
        .order_by(desc(NewsArticle.date), desc(NewsArticle.id))
        .limit(3)
        .all()
    )

    return {
        "city": city,
        "items": [
            {
                "date": r.date.isoformat(),
                "headline": r.title,
                "sentiment": r.sentiment_label,
                "url": r.url,
            }
            for r in rows
        ],
    }

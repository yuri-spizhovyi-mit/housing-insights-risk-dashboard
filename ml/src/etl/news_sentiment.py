"""
ETL for housing-related news sentiment.
Now delegates sentiment scoring to ml/src/models/nlp/sentiment_model.py
"""

import os
import pandas as pd
import feedparser
from ml.src.nlp.sentiment_model import score_text  # ✅ new import
from . import base
from datetime import datetime
from sqlalchemy import text

SNAPSHOT_DIR = "./.debug/news"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

FEEDS = {
    "Victoria": [
        "https://globalnews.ca/tag/victoria-real-estate/feed/",
        "https://www.timescolonist.com/rss",  # includes real estate / local housing
    ],
    "Vancouver": [
        "https://globalnews.ca/tag/vancouver-real-estate/feed/",
        "https://vancouversun.com/category/real-estate/feed",
    ],
    "Calgary": [
        "https://globalnews.ca/tag/calgary-real-estate/feed/",
        "https://calgaryherald.com/category/real-estate/feed",
    ],
    "Edmonton": [
        "https://globalnews.ca/tag/edmonton-real-estate/feed/",
        "https://edmontonjournal.com/category/real-estate/feed",
    ],
    "Winnipeg": [
        "https://globalnews.ca/tag/winnipeg-real-estate/feed/",
        "https://winnipegsun.com/category/real-estate/feed",
    ],
    "Ottawa": [
        "https://globalnews.ca/tag/ottawa-real-estate/feed/",
        "https://ottawacitizen.com/category/real-estate/feed",
    ],
    "Toronto": [
        "https://globalnews.ca/tag/toronto-real-estate/feed/",
        "https://toronto.ctvnews.ca/rss/Real-Estate",
    ],
}


def fetch_news() -> pd.DataFrame:
    """Fetch RSS feeds and apply sentiment model."""
    records = []
    for city, urls in FEEDS.items():
        for url in urls:
            feed = feedparser.parse(url)
            for e in feed.entries:
                score, label = score_text(e.title)  # ✅ model call
                date_val = pd.to_datetime(
                    getattr(e, "published", None), errors="coerce"
                )
                if pd.isna(date_val):
                    date_val = pd.Timestamp.today()
                records.append(
                    {
                        "date": date_val.date(),
                        "city": city,
                        "title": e.title,
                        "url": e.link,
                        "sentiment_score": score,
                        "sentiment_label": label,
                    }
                )
    return pd.DataFrame(records)


def update_news_sentiment(ctx_or_engine):
    """Aggregate daily sentiment (same as before)."""
    engine = getattr(ctx_or_engine, "engine", ctx_or_engine)
    with engine.begin() as conn:
        df = pd.read_sql(
            text(
                "SELECT date, city, sentiment_score FROM news_articles WHERE date IS NOT NULL"
            ),
            conn,
        )

    if df.empty:
        print("No data to aggregate for news_sentiment.")
        return {"rows": 0}

    agg = df.groupby(["date", "city"], as_index=False)["sentiment_score"].mean()
    agg["sentiment_score"] = agg["sentiment_score"].round(2)
    agg["sentiment_label"] = agg["sentiment_score"].apply(
        lambda s: "POS" if s > 0.05 else "NEG" if s < -0.05 else "NEU"
    )

    with engine.begin() as conn:
        for _, row in agg.iterrows():
            conn.execute(
                text("""
                    INSERT INTO news_sentiment (date, city, sentiment_score, sentiment_label)
                    VALUES (:date, :city, :score, :label)
                    ON CONFLICT (date, city)
                    DO UPDATE SET
                        sentiment_score = EXCLUDED.sentiment_score,
                        sentiment_label = EXCLUDED.sentiment_label;
                """),
                {
                    "date": row["date"],
                    "city": row["city"],
                    "score": row["sentiment_score"],
                    "label": row["sentiment_label"],
                },
            )
    return {"rows": len(agg)}


def run(ctx):
    df = fetch_news()
    if df.empty:
        print("No news fetched.")
        return {"rows": 0}

    df.to_csv(f"{SNAPSHOT_DIR}/news_articles_raw.csv", index=False)
    base.write_df(df, "news_articles", ctx)
    neon_engine = base.get_neon_engine()
    base.write_df(df, "news_articles", neon_engine)

    # Cleanup
    for engine in [ctx.engine, neon_engine]:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "DELETE FROM news_articles WHERE date < CURRENT_DATE - INTERVAL '90 days';"
                )
            )

    update_news_sentiment(ctx)
    update_news_sentiment(neon_engine)
    return {"rows": len(df)}

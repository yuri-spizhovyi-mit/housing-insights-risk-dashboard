"""
ETL for housing-related news sentiment.

Workflow:
1. Fetch headlines from configured RSS feeds.
2. Insert raw rows into `news_articles` (for UI display).
   - Each headline carries its own sentiment score + label.
3. Aggregate daily sentiment by (date, city) from `news_articles`
   and insert into `news_sentiment` (for ML models).
"""

import os
import pandas as pd
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from . import base
from datetime import timedelta
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert


SNAPSHOT_DIR = "./.debug/news"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# RSS feeds per city (you can extend/change as needed)
FEEDS = {
    "Kelowna": [
        "https://globalnews.ca/tag/kelowna-real-estate/feed/",
        "https://okanaganedge.net/feed/",
    ],
    "Vancouver": [
        "https://globalnews.ca/tag/vancouver-real-estate/feed/",
        "https://vancouversun.com/category/real-estate/feed",
    ],
    "Toronto": [
        "https://globalnews.ca/tag/toronto-real-estate/feed/",
        "https://toronto.ctvnews.ca/rss/Real-Estate",
    ],
}

analyzer = SentimentIntensityAnalyzer()


def fetch_news() -> pd.DataFrame:
    """
    Fetch headlines from configured RSS feeds, analyze sentiment,
    and return a DataFrame with raw article records.
    """
    records = []
    for city, urls in FEEDS.items():
        for url in urls:
            feed = feedparser.parse(url)
            for e in feed.entries:
                score = analyzer.polarity_scores(e.title)["compound"]
                label = "POS" if score > 0.05 else "NEG" if score < -0.05 else "NEU"
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
                        "sentiment_score": round(score, 2),
                        "sentiment_label": label,
                    }
                )
    return pd.DataFrame(records)


def update_news_sentiment(ctx_or_engine):
    """
    Aggregate daily sentiment from `news_articles` into `news_sentiment`.
    Uses daily average sentiment_score per (city, date).
    Also derives sentiment_label from the average score.
    Performs UPSERT to avoid duplicate key violations.
    Accepts either a Context (with .engine) or a raw SQLAlchemy engine.
    """
    # Normalize to engine
    engine = getattr(ctx_or_engine, "engine", ctx_or_engine)

    with engine.begin() as conn:
        df = pd.read_sql(
            text("""
                SELECT date, city, sentiment_score
                FROM news_articles
                WHERE date IS NOT NULL
            """),
            conn,
        )

    if df.empty:
        print("No data to aggregate for news_sentiment.")
        return {"rows": 0}

    # Aggregate mean score
    agg = df.groupby(["date", "city"], as_index=False).agg({"sentiment_score": "mean"})
    agg["sentiment_score"] = agg["sentiment_score"].round(2)

    # Derive label from average score
    def score_to_label(score):
        if score > 0.05:
            return "POS"
        elif score < -0.05:
            return "NEG"
        return "NEU"

    agg["sentiment_label"] = agg["sentiment_score"].apply(score_to_label)

    agg.to_csv(f"{SNAPSHOT_DIR}/news_sentiment_daily.csv", index=False)

    # ---- Upsert into news_sentiment ----
    with engine.begin() as conn:
        for _, row in agg.iterrows():
            conn.execute(
                text("""
                    INSERT INTO news_sentiment (date, city, sentiment_score, sentiment_label)
                    VALUES (:date, :city, :score, :label)
                    ON CONFLICT (date, city)
                    DO UPDATE SET sentiment_score = EXCLUDED.sentiment_score,
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

    # Save raw snapshot for debugging
    df.to_csv(f"{SNAPSHOT_DIR}/news_articles_raw.csv", index=False)

    # Insert into local DB
    base.write_df(df, "news_articles", ctx)

    # Insert into Neon DB
    neon_engine = base.get_neon_engine()
    base.write_df(df, "news_articles", neon_engine)

    # Keep only 90 days in both
    with ctx.engine.begin() as conn:
        conn.execute(text("DELETE FROM news_articles WHERE date < CURRENT_DATE - INTERVAL '90 days';"))
    with neon_engine.begin() as conn:
        conn.execute(text("DELETE FROM news_articles WHERE date < CURRENT_DATE - INTERVAL '90 days';"))

    # Aggregate for ML and push to both
    update_news_sentiment(ctx)                # local
    update_news_sentiment(neon_engine)        # Neon



if __name__ == "__main__":
    from types import SimpleNamespace
    from . import db

    ctx = SimpleNamespace(engine=db.get_engine(), params={})
    output = run(ctx)
    print(output)

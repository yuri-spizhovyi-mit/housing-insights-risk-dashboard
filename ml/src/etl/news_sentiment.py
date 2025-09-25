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
        "https://www.thestar.com/content/thestar/feed.RSSManagerServlet.articles.realestate.rss",
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


def update_news_sentiment(ctx):
    """
    Aggregate daily sentiment from `news_articles` into `news_sentiment`.
    Uses daily average sentiment_score per (city, date).
    """
    from sqlalchemy import text

    with ctx.engine.begin() as conn:
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

    agg = df.groupby(["date", "city"], as_index=False).agg({"sentiment_score": "mean"})
    agg["sentiment_score"] = agg["sentiment_score"].round(2)

    agg.to_csv(f"{SNAPSHOT_DIR}/news_sentiment_daily.csv", index=False)
    base.write_df(agg, "news_sentiment", ctx)

    return {"rows": len(agg)}


def run(ctx):
    """
    Main ETL entrypoint.
    - Fetch raw headlines from feeds.
    - Insert into `news_articles`.
    - Aggregate from `news_articles` into `news_sentiment`.
    """
    df = fetch_news()
    if df.empty:
        print("No news fetched.")
        return {"rows": 0}

    # Save raw headlines
    df.to_csv(f"{SNAPSHOT_DIR}/news_articles_raw.csv", index=False)
    base.write_df(df, "news_articles", ctx)

    # Aggregate for ML
    result = update_news_sentiment(ctx)
    return result


if __name__ == "__main__":
    from types import SimpleNamespace
    from . import db

    ctx = SimpleNamespace(engine=db.get_engine(), params={})
    output = run(ctx)
    print(output)

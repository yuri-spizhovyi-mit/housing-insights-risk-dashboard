"""
Fetch real-estate related news headlines, run sentiment analysis,
insert raw headlines into `news_articles` (for UI),
aggregate by (date, city), and insert into `news_sentiment` (for ML).
"""

import os
import pandas as pd
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from . import base

SNAPSHOT_DIR = "./.debug/news"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

FEEDS = {
    "Kelowna": [
        "https://globalnews.ca/tag/kelowna-real-estate/feed/",
        "https://okanaganedge.net/feed/",  # local business/real estate
    ],
    "Vancouver": [
        "https://globalnews.ca/tag/vancouver-real-estate/feed/",
        "https://vancouversun.com/category/real-estate/feed",
    ],
    "Toronto": [
        "https://globalnews.ca/tag/toronto-real-estate/feed/",
        "https://torontostar.com/feed/",  # Toronto Star real estate
    ],
}


analyzer = SentimentIntensityAnalyzer()


def fetch_news():
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
                records.append(
                    {
                        "date": pd.to_datetime(
                            getattr(e, "published", None), errors="coerce"
                        ).date(),
                        "city": city,
                        "title": e.title,
                        "url": e.link,
                        "sentiment_score": round(score, 2),
                        "sentiment_label": label,
                    }
                )
    return pd.DataFrame(records)


def run(ctx):
    """
    Main ETL entrypoint.
    - Fetch raw headlines.
    - Insert raw rows into `news_articles`.
    - Aggregate sentiment by (date, city) and write to `news_sentiment`.
    """
    df = fetch_news()
    if df.empty:
        print("No news fetched.")
        return {"rows": 0}

    # ---- Save raw headlines (UI) ----
    df.to_csv(f"{SNAPSHOT_DIR}/news_articles_raw.csv", index=False)
    base.write_df(df, "news_articles", ctx)

    # ---- Aggregate by (date, city) (ML) ----
    agg = df.groupby(["date", "city"], as_index=False).agg({"sentiment_score": "mean"})
    agg["sentiment_score"] = agg["sentiment_score"].round(2)

    agg.to_csv(f"{SNAPSHOT_DIR}/news_sentiment_daily.csv", index=False)
    base.write_df(agg, "news_sentiment", ctx)

    return {"rows": len(agg)}


if __name__ == "__main__":
    from types import SimpleNamespace
    from . import db

    ctx = SimpleNamespace(engine=db.get_engine(), params={})
    result = run(ctx)
    print(result)

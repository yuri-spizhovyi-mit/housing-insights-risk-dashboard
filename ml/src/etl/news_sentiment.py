"""
Fetch real-estate related news headlines, run sentiment,
aggregate by (date, city), and load into news_sentiment table.
"""

import os
import pandas as pd
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from . import base

SNAPSHOT_DIR = "./.debug/news"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

FEEDS = [
    "https://globalnews.ca/tag/vancouver-real-estate/feed/",
    "https://vancouversun.com/category/real-estate/feed",
]

analyzer = SentimentIntensityAnalyzer()


def fetch_news():
    records = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries:
            score = analyzer.polarity_scores(e.title)["compound"]
            label = (
                "Positive"
                if score > 0.05
                else "Negative"
                if score < -0.05
                else "Neutral"
            )
            records.append(
                {
                    "date": pd.to_datetime(e.published, errors="coerce").date(),
                    "city": "Vancouver",
                    "sentiment_score": score,
                    "sentiment_label": label,
                }
            )
    return pd.DataFrame(records)


def run(ctx):
    df = fetch_news()
    if df.empty:
        print("No news fetched.")
        return {"rows": 0}

    # ---- Aggregate by (date, city) ----
    agg = df.groupby(["date", "city"], as_index=False).agg(
        {
            "sentiment_score": "mean",
            "sentiment_label": lambda x: x.mode()[0]
            if not x.mode().empty
            else "Neutral",
        }
    )

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

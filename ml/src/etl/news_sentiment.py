"""
Fetch real-estate related news headlines, run sentiment, and load into news_sentiment table.
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
                    "city": "Vancouver",  # static for now, could parse from feed if multi-city
                    "sentiment_score": round(score, 2),
                    "sentiment_label": label,
                }
            )
    return pd.DataFrame(records)


def run(ctx):
    df = fetch_news()
    df.to_csv(f"{SNAPSHOT_DIR}/news_sentiment.csv", index=False)
    # Only write the required cols
    df = df[["date", "city", "sentiment_score", "sentiment_label"]]
    base.write_df(df, "news_sentiment", ctx)
    return {"rows": len(df)}

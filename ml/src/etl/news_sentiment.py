"""
Fetch real-estate related news headlines, run sentiment, and load into news_sentiment.
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
                    "date": pd.to_datetime(e.published, errors="coerce"),
                    "city": "Vancouver",
                    "sentiment_score": score,
                    "sentiment_label": label,
                    "title": e.title,
                }
            )
    return pd.DataFrame(records)


def run(ctx):
    df = fetch_news()
    df.to_csv(f"{SNAPSHOT_DIR}/news_raw.csv", index=False)
    base.write_df(df, "news_sentiment", ctx)
    return {"rows": len(df)}

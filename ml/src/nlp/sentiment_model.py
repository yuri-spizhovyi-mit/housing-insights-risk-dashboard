from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def score_text(text: str):
    """Return (sentiment_score, sentiment_label)."""
    if not text:
        return 0.0, "NEU"

    score = analyzer.polarity_scores(text)["compound"]
    label = "POS" if score > 0.05 else "NEG" if score < -0.05 else "NEU"
    return round(score, 2), label

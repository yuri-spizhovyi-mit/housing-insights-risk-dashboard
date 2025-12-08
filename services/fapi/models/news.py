from sqlalchemy import Column, Integer, String, Date, Text, Numeric
from services.fapi.db import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    city = Column(String(100))
    title = Column(Text, nullable=False)
    url = Column(Text)
    sentiment_score = Column(Numeric(5, 2))
    sentiment_label = Column(String(20))

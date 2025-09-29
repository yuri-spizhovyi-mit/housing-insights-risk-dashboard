export type SentimentValue = "NEG" | "NEU" | "POS";

export type Sentiment = {
  date: string;
  headline: string;
  sentiment: SentimentValue;
  url: string;
};

export type CitySentiments = {
  city: string;
  items: Sentiment[];
};

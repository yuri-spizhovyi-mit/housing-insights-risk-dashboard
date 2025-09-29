export type SentimentsData = {
  city: string;
  items: Array<SentimentData>;
};

export type SentimentData = {
  date: string;
  headline: string;
  sentiment: "NEG" | "NEU" | "POS";
  url: string;
};

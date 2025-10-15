export type MarketAnomaly = {
  date: string;
  score: number;
  is_anomaly: boolean;
};

export type MarketAnomaliesSeries = {
  city: string;
  target: "price" | "rent";
  signals: MarketAnomaly[];
};

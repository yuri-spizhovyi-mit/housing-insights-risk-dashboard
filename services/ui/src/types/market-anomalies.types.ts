export type MarketAnomaliesSeries = {
  city: string;
  target: string;
  signals: MarketAnomaly[];
};

export type MarketAnomaly = {
  date: string;
  anomaly: number;
  is_anomaly: boolean;
};

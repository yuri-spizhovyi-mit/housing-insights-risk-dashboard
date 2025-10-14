export type ForecastPoint = {
  date: string;
  value: number;
  lower: number;
  upper: number;
};

export type Forecast = {
  city: string;
  target: string;
  horizon: number;
  data: ForecastPoint[];
};

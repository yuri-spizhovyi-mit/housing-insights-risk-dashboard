import type { RequestModelType } from "../context/FilterContext";

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
  modelType: RequestModelType;
  data: ForecastPoint[];
};

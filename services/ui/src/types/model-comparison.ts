export interface HorizonMetric {
  horizon: number;
  mae: number;
  mape: number;
  rmse: number;
  mse: number;
  r2: number | null;
}

export interface ModelMetricsMap {
  arima?: HorizonMetric[];
  lstm?: HorizonMetric[];
  prophet?: HorizonMetric[];
  [modelName: string]: HorizonMetric[] | undefined;
}

export interface ForecastMetricsResponse {
  city: string;
  target: string;
  horizons: number[];
  models: ModelMetricsMap;
}

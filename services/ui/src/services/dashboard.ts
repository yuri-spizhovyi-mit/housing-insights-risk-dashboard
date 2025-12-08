import type { CitySentiments } from "../types/sentiments";
import type { State } from "../context/FilterContext";
import { ApiError } from "./errors";

import type { MarketAnomaliesSeries } from "../types/market-anomalies";
import type { CityInsight } from "../types/risk";
import type { ForecastMetricsResponse } from "../types/model-comparison";

export async function getCities(): Promise<string[]> {
  const res = await fetch(
    "https://housing-insights-risk-dashboard.vercel.app/cities"
  );

  if (!res.ok) {
    throw new Error("Failed to fetch cities.");
  }

  const data = await res.json();
  return data.cities;
}

export type ForecastTarget = "price" | "rent";

export async function getForecast(filters: State, target: ForecastTarget) {
  const params = new URLSearchParams();
  params.append("city", filters.city);
  params.append("horizon", filters.horizon.toLowerCase());
  params.append("target", target);
  params.append("model", filters.modelType.toLowerCase());

  let res: Response;
  try {
    res = await fetch(
      `https://housing-insights-risk-dashboard.vercel.app/forecast?${params.toString()}&`
    );
  } catch {
    throw new ApiError(
      "error",
      "Failed to fetch forecast",
      "Could not reach the forecast server. Please check your connection."
    );
  }

  if (res.status === 404) {
    throw new ApiError(
      "empty",
      "No forecast data available",
      `We don’t have results for ${filters.city},  horizon:${filters.horizon}Y, and model type:${filters.modelType}. Try adjusting filters.`
    );
  }

  if (!res.ok) {
    throw new ApiError(
      "error",
      "Something went wrong",
      "Server is unavailable, please try again later."
    );
  }

  const data = await res.json();
  return data;
}

export async function getSentiments(city: string): Promise<CitySentiments> {
  try {
    const res = await fetch(
      `https://housing-insights-risk-dashboard.vercel.app/sentiment?city=${city}`
    );

    if (!res.ok) {
      throw new ApiError(
        "error",
        "Something went wrong",
        "Server is unavailable, please try again later."
      );
    }

    const data = await res.json();

    if (!data || typeof data !== "object") {
      throw new ApiError(
        "error",
        "Invalid response from server",
        "Sentiment data is missing or improperly formatted."
      );
    }

    return data;
  } catch (err) {
    if (err instanceof ApiError) throw err;

    throw new ApiError(
      "error",
      "Failed to fetch",
      "Network request failed or the server is unreachable."
    );
  }
}

export async function getRiskGauge(city: string): Promise<CityInsight> {
  try {
    const res = await fetch(
      `https://housing-insights-risk-dashboard.vercel.app/risk?city=${city}`
    );

    if (!res.ok) {
      throw new ApiError(
        "error",
        "Something went wrong",
        "Server is unavailable, please try again later."
      );
    }

    const data = await res.json();

    if (!data || typeof data !== "object") {
      throw new ApiError(
        "error",
        "Invalid response from server",
        "Risk gauge data is missing or incomplete."
      );
    }

    return data;
  } catch (err) {
    if (err instanceof ApiError) throw err;

    throw new ApiError(
      "error",
      "Failed to fetch",
      "Network request failed or the server is unreachable."
    );
  }
}

export async function getMarketAnomalies(
  city: string
): Promise<MarketAnomaliesSeries[]> {
  try {
    const res = await Promise.all([
      fetch(
        `https://housing-insights-risk-dashboard.vercel.app/anomalies?city=${city}&target=rent`
      ),
      fetch(
        `https://housing-insights-risk-dashboard.vercel.app/anomalies?city=${city}&target=price`
      ),
    ]);

    if (res.some((r) => r.status === 404)) {
      throw new ApiError(
        "empty",
        `No market anomaly data found for ${city}.`,
        `We don't have anomaly insights for this city yet — our models are still training. 
        Please check back soon or try selecting another location.`
      );
    }

    if (!res.some((r) => r.ok)) {
      throw new ApiError(
        "error",
        "Something went wrong",
        "Server is unavailable, please try again later."
      );
    }

    const data: MarketAnomaliesSeries[] = await Promise.all(
      res.map((r) => r.json() as Promise<MarketAnomaliesSeries>)
    );

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    throw new ApiError(
      "error",
      "Network failure",
      `Unable to fetch anomaly data for ${city}. Please check your internet connection or try again later.\n${String(
        error
      )}`
    );
  }
}

export async function getModelComparisons(
  city: string,
  target: ForecastTarget
): Promise<ForecastMetricsResponse> {
  try {
    const res = await fetch(
      `https://housing-insights-risk-dashboard.vercel.app/model-comparison?city=${city}&target=${target}`
    );

    if (res.status === 404) {
      throw new ApiError(
        "empty",
        "No model comparison data available",
        `We don’t have results for ${city} and target: ${target}. Try adjusting filters.`
      );
    }

    if (!res.ok) {
      throw new ApiError(
        "error",
        "Something went wrong",
        "Server is unavailable, please try again later."
      );
    }

    const data = await res.json();

    if (!data || !data.models) {
      throw new ApiError(
        "error",
        "Invalid response from server",
        "The model data format is incorrect or incomplete."
      );
    }

    return data;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }

    throw new ApiError(
      "error",
      "Failed to fetch",
      "Network request failed or the server is unreachable."
    );
  }
}

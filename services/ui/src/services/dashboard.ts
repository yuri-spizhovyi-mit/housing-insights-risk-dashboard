import type { CitySentiments } from "../types/sentiments";
import type { FilterContextType } from "../context/FilterContext";
import { ApiError } from "./errors";

import type { MarketAnomaliesSeries } from "../types/market-anomalies";
import type { CityInsight } from "../types/risk";

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

export async function getForecast(filters: FilterContextType) {
  const params = new URLSearchParams();
  params.append("city", filters.city);
  params.append("horizon", filters.horizon.toLowerCase());
  params.append("target", filters.target);
  params.append("sqftMin", String(filters.sqftMin));
  params.append("sqftMax", String(filters.sqftMax));

  if (filters.propertyType && filters.propertyType !== "Any") {
    params.append("propertyType", filters.propertyType);
  }
  if (filters.beds && filters.beds !== "Any") {
    params.append("beds", filters.beds);
  }
  if (filters.baths && filters.baths !== "Any") {
    params.append("baths", filters.baths);
  }

  let res: Response;
  try {
    res = await fetch(
      `https://housing-insights-risk-dashboard.vercel.app/forecast?${params.toString()}`
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
      `We don’t have results for ${filters.city}, ${filters.propertyType}, max:${filters.sqftMin} - min:${filters.sqftMax} sqft, horizon:${filters.horizon}Y. Try adjusting filters.`
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
  return data;
}

export async function getRiskGauge(city: string): Promise<CityInsight> {
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
  return data;
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

import type { FilterContextType } from "../context/FilterContext";

type CitiesResponse = {
  cities: string[];
};

export async function getCities(): Promise<string[]> {
  const res = await fetch(
    "https://housing-insights-risk-dashboard.vercel.app/cities"
  );

  if (!res.ok) {
    throw new Error(`Failed to fetch cities.`);
  }

  const data: CitiesResponse = await res.json();
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

  const url = `https://housing-insights-risk-dashboard.vercel.app/forecast?${params.toString()}`;
  console.log(url);
  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`Forecast, for city ${filters.city} request failed!`);
    console.clear();
    console.error(`Forecast request failed: ${res.status}`);
    console.log(res);
  }

  return res.json();
}

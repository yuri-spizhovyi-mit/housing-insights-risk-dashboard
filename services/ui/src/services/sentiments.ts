import type { SentimentsData } from "../types/sentiments.types";

export async function getSentiments(city: string): Promise<SentimentsData> {
  const res = await fetch(
    `https://housing-insights-risk-dashboard.vercel.app/sentiment?city=${city}`
  );
  console.log(city);

  if (!res.ok) {
    throw new Error("Failed to fetch sentiments.");
  }

  const data = await res.json();
  return data;
}

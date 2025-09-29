import type { SentimentsData } from "../types/sentiments.types";
import { ApiError } from "./errors";

export async function getSentiments(city: string): Promise<SentimentsData> {
  const res = await fetch(
    `https://housing-insights-risk-dashboard.vercel.app/sentiment?city=${city}`
  );
  console.log(city);

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

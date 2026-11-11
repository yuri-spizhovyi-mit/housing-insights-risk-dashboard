import { z } from "zod";
export const base = (
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? "/api" : "https://housing-insights-risk-dashboard.vercel.app")
).replace(/\/$/, "");
export const pointSchema = z
  .object({
    date: z.iso.date(),
    value: z.number().finite(),
    lower: z.number().finite().nullable().default(null),
    upper: z.number().finite().nullable().default(null),
  })
  .refine(
    (p) =>
      (p.lower === null || p.lower <= p.value) &&
      (p.upper === null || p.upper >= p.value),
    "Invalid forecast bounds",
  );
export const forecastSchema = z
  .object({
    city: z.string(),
    target: z.enum(["price", "rent"]),
    horizon: z.number().int().positive(),
    model: z.string(),
    data: z.array(pointSchema),
  })
  .refine(
    (r) => r.data.every((p, i) => i === 0 || p.date > r.data[i - 1].date),
    "Forecast dates must be unique and ordered",
  );
export type Forecast = z.infer<typeof forecastSchema>;
export type Filters = {
  city: string;
  target: "price" | "rent";
  horizon: "1y" | "2y" | "5y";
  model: "arima" | "prophet" | "lstm";
};
export const riskSchema = z.object({
  city: z.string(),
  date: z.iso.date(),
  breakdown: z.array(z.object({ name: z.string(), status: z.string() })),
});
export type Risk = z.infer<typeof riskSchema>;
export class ApiError extends Error {
  status: number;
  constructor(
    status: number,
    message: string,
  ) {
    super(message);
    this.status=status;
  }
}
export async function request(
  path: string,
  signal?: AbortSignal,
): Promise<unknown> {
  const response = await fetch(base + path, {
    signal: AbortSignal.any([
      AbortSignal.timeout(15000),
      ...(signal ? [signal] : []),
    ]),
  });
  if (!response.ok)
    throw new ApiError(
      response.status,
      response.status === 404
        ? "No data is available for this selection."
        : "Unable to load market data. Please retry.",
    );
  return response.json();
}
export function readFilters(search: string): Filters {
  const p = new URLSearchParams(search);
  return {
    city: p.get("city")?.trim() || "Calgary",
    target: p.get("target") === "rent" ? "rent" : "price",
    horizon:
      p.get("horizon") === "2y"
        ? "2y"
        : p.get("horizon") === "5y"
          ? "5y"
          : "1y",
    model:
      p.get("model") === "prophet"
        ? "prophet"
        : p.get("model") === "lstm"
          ? "lstm"
          : "arima",
  };
}
export const forecastKey = (filters: Filters) =>
  [
    "forecast-mvp",
    filters.city,
    filters.target,
    filters.horizon,
    filters.model,
  ] as const;
export async function getForecast(filters: Filters, signal?: AbortSignal) {
  const parsed = forecastSchema.parse(
    await request("/forecast?" + new URLSearchParams(filters), signal),
  );
  if (
    parsed.city.toLowerCase() !== filters.city.toLowerCase() ||
    parsed.target !== filters.target ||
    parsed.model !== filters.model ||
    parsed.horizon !== { "1y": 12, "2y": 24, "5y": 60 }[filters.horizon]
  )
    throw new Error("The server returned data for different filters.");
  return parsed;
}
export async function getRisk(city: string, signal?: AbortSignal) {
  const data = riskSchema.parse(
    await request("/risk?" + new URLSearchParams({ city }), signal),
  );
  if (data.city.toLowerCase() !== city.toLowerCase())
    throw new Error("Risk data does not match the selected city.");
  return data;
}
export async function getCities(signal?: AbortSignal) {
  return z
    .object({ cities: z.array(z.string()) })
    .parse(await request("/cities", signal)).cities;
}

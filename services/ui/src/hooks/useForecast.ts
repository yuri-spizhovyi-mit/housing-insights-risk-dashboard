import { useQuery } from "@tanstack/react-query";
import type { State } from "../context/FilterContext";
import { getForecast } from "../services/dashboard";
import type { ApiError } from "../services/errors";
import type { ForecastResponse } from "../types/forecast.types";

export function useForecast(filters: State, target: "price" | "rent") {
  const { data, error, isFetching } = useQuery<ForecastResponse, ApiError>({
    queryKey: ["forecast"],
    queryFn: () => getForecast({ ...filters, target }),
  });

  return { forecast: data, error, isFetching };
}

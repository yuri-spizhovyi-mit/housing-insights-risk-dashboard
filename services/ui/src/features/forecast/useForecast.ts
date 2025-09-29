import { useQuery } from "@tanstack/react-query";
import type { State } from "../../context/FilterContext";
import type { Forecast } from "../../types/forecast.types";
import type { ApiError } from "../../services/errors";
import { getForecast } from "../../services/dashboard";

export function useForecast(filters: State, target: "price" | "rent") {
  const { data, error, isFetching } = useQuery<Forecast, ApiError>({
    queryKey: ["forecast"],
    queryFn: () => getForecast({ ...filters, target }),
  });

  return { forecast: data, error, isFetching };
}

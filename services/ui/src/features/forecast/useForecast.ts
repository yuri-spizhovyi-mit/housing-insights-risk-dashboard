import { useQuery } from "@tanstack/react-query";
import type { State } from "../../context/FilterContext";
import type { Forecast } from "../../types/forecast";
import type { ApiError } from "../../services/errors";
import { getForecast, type ForecastTarget } from "../../services/dashboard";

export function useForecast(filters: State, target: ForecastTarget) {
  const { data, error, isFetching } = useQuery<Forecast, ApiError>({
    queryKey: [`forecast-${target}`],
    queryFn: () => getForecast(filters, target),
  });

  return { forecast: data, error, isFetching };
}

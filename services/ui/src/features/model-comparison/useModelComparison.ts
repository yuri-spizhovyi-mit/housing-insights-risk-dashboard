import { useQuery } from "@tanstack/react-query";
import type { ApiError } from "../../services/errors";
import {
  getModelComparisons,
  type ForecastTarget,
} from "../../services/dashboard";
import type { ForecastMetricsResponse } from "../../types/model-comparison";

export function useModelComparison(city: string, target: ForecastTarget) {
  const { data, error, isFetching } = useQuery<
    ForecastMetricsResponse,
    ApiError
  >({
    queryKey: [`model-comparison-${target}`],
    queryFn: () => getModelComparisons(city, target),
  });

  return { modelsData: data, error, isFetching };
}

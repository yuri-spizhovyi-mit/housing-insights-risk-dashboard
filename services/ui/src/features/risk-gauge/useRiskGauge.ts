import { useQuery } from "@tanstack/react-query";
import { getRiskGauge } from "../../services/dashboard";
import type { CityInsight } from "../../types/risk";
import type { ApiError } from "../../services/errors";

export function useRiskGauge(city: string) {
  const {
    data: risk,
    error,
    isFetching,
  } = useQuery<CityInsight, ApiError>({
    queryKey: ["risk-gauge"],
    queryFn: () => getRiskGauge(city),
  });
  return { risk, error, isFetching };
}

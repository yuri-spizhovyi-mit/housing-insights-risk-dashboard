import type { MarketAnomaliesSeries } from "../../types/market-anomalies";
import { getMarketAnomalies } from "../../services/dashboard";
import type { ApiError } from "../../services/errors";
import { useQuery } from "@tanstack/react-query";

export function useMarketAnomalies(target: string) {
  const {
    data: marketAnomalies,
    error,
    isFetching,
  } = useQuery<MarketAnomaliesSeries[], ApiError>({
    queryKey: ["market-anomalies"],
    queryFn: () => getMarketAnomalies(target),
  });

  return { marketAnomalies, isFetching, error };
}

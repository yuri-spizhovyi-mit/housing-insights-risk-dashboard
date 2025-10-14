import { useQuery } from "@tanstack/react-query";
import type { ApiError } from "../../services/errors";
import { getSentiments } from "../../services/dashboard";
import type { CitySentiments } from "../../types/sentiments";

export function useSentiments(city: string) {
  const {
    data: sentiments,
    error,
    isFetching,
  } = useQuery<CitySentiments, ApiError>({
    queryKey: ["sentiments"],
    queryFn: () => getSentiments(city),
  });

  return { sentiments, error, isFetching };
}

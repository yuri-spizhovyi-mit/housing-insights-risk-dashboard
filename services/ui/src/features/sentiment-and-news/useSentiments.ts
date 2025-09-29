import { useQuery } from "@tanstack/react-query";
import type { SentimentsData } from "../../types/sentiments.types";
import { getSentiments } from "../../services/sentiments";
import type { ApiError } from "../../services/errors";

export function useSentiments(city: string) {
  const {
    data: sentiments,
    error,
    isFetching,
  } = useQuery<SentimentsData, ApiError>({
    queryKey: ["sentiments"],
    queryFn: () => getSentiments(city),
  });

  return { sentiments, error, isFetching };
}

import { useQuery } from "@tanstack/react-query";
import { getCities } from "../../services/dashboard";

export function useCities() {
  const {
    data: cities,
    error,
    isPending,
  } = useQuery({
    queryKey: ["cities-options"] as const,
    queryFn: getCities,
  });

  return { cities, error, isPending };
}

import { useQuery } from "@tanstack/react-query";
import type { State } from "../../context/FilterContext";
import { getForecast } from "../../services/dashboard";

export function useHomePriceForecast(filters: State) {
  const { data, error, isFetching } = useQuery({
    queryKey: ["forecast"],
    queryFn: () => getForecast({ ...filters, target: "price" }),
  });

  return { forecast: data, error, isFetching };
}

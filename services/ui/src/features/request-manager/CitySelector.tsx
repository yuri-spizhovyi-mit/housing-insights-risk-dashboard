import { MapPin } from "lucide-react";
import { useCities } from "./useCities";
import { useFilters } from "../../context/FilterContext";

import SelectorShell from "./SelectorShell";
import FilterSelector from "./FilterSelector";

function CitySelector() {
  const { dispatch, city } = useFilters();
  const { cities, isPending, error } = useCities();

  const handleCityChange = (newCity: string) => {
    dispatch({ type: "SET_CITY", payload: newCity });
  };

  return (
    <SelectorShell
      leftIcon={<MapPin className="size-4 opacity-70" />}
      className="px-4"
      type="City"
    >
      {isPending && <p className="text-sm text-gray-500">Fetching...</p>}
      {error && <p className="text-sm text-red-500">Failed to load cities.</p>}
      {!isPending && !error && cities && cities.length > 0 && (
        <FilterSelector
          value={city}
          data={cities}
          handleValueUpdate={handleCityChange}
        />
      )}
    </SelectorShell>
  );
}

export default CitySelector;

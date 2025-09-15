import { MapPin } from "lucide-react";

import SelectorShell from "./SelectorShell";
import FilterSelector from "./FilterSelector";
import { useFilters } from "../../context/FilterContext";

function CitySelector() {
  const { dispatch, city } = useFilters();
  const cities = ["Kelowna", "Vancouver", "Toronto"];

  return (
    <SelectorShell
      leftIcon={<MapPin className="size-4 opacity-70" />}
      className="px-4"
      type="City"
    >
      <FilterSelector
        value={city}
        data={cities}
        handleValueUpdate={(city: string) =>
          dispatch({ type: "SET_CITY", payload: city })
        }
      />
    </SelectorShell>
  );
}

export default CitySelector;

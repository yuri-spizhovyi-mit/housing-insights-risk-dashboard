import SelectorShell from "./SelectorShell";
import { useFilters } from "../../context/FilterContext";
import FilterSelector from "./FilterSelector";

function PropertyTypeSelector() {
  const propertyTypes = ["Condo", "House", "Town House", "Apartment"];

  const { dispatch, propertyType } = useFilters();

  return (
    <SelectorShell type="Property Type" className="px-4">
      <FilterSelector
        value={propertyType}
        data={propertyTypes}
        handleValueUpdate={(property: string) =>
          dispatch({ type: "SET_PROPERTY_TYPE", payload: property })
        }
      />
    </SelectorShell>
  );
}

export default PropertyTypeSelector;

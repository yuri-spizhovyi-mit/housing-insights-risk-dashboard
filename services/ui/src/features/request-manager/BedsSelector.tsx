import SelectorShell from "./SelectorShell";
import { useFilters } from "../../context/FilterContext";
import FilterSelector from "./FilterSelector";

function BedsSelector() {
  const { dispatch, beds } = useFilters();
  const quant = ["Any", "1", "2", "3"];

  return (
    <SelectorShell type="Beds" className="px-6">
      <FilterSelector
        value={beds}
        data={quant}
        handleValueUpdate={(beds: string) =>
          dispatch({ type: "SET_BEDS", payload: beds })
        }
      />
    </SelectorShell>
  );
}

export default BedsSelector;

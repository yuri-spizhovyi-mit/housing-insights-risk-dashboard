import SelectorShell from "./SelectorShell";
import FilterSelector from "./FilterSelector";
import { useFilters } from "../../context/FilterContext";

function BathsSelector() {
  const { dispatch, baths } = useFilters();
  const quant = ["Any", "1", "2", "3+"];

  return (
    <SelectorShell type="Baths" className="px-4">
      <FilterSelector
        value={baths}
        data={quant}
        handleValueUpdate={(baths: string) =>
          dispatch({ type: "SET_PROPERTY_TYPE", payload: baths })
        }
      />
    </SelectorShell>
  );
}

export default BathsSelector;

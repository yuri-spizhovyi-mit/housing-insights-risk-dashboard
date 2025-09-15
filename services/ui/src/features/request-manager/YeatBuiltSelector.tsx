import SelectorShell from "./SelectorShell";
import { useFilters } from "../../context/FilterContext";
import FilterSelector from "./FilterSelector";

function YeatBuiltSelector() {
  const { dispatch, yearBuilt } = useFilters();
  const quant = ["Any", "2000+", "2010+", "2020+"];

  return (
    <SelectorShell type="Year Built" className="px-4">
      <FilterSelector
        value={yearBuilt}
        data={quant}
        handleValueUpdate={(year: string) =>
          dispatch({ type: "SET_YEAR_BUILT", payload: year })
        }
      />
    </SelectorShell>
  );
}

export default YeatBuiltSelector;

import SelectorShell from "./SelectorShell";
import { useFilters } from "../../context/FilterContext";

function SqrtRangeSelector() {
  const { dispatch, sqftMin, sqftMax } = useFilters();

  return (
    <SelectorShell className="px-4">
      <label className="opacity-70">Sqft</label>
      <div className="flex items-center gap-2">
        <input
          type="range"
          min={300}
          max={5000}
          step={50}
          value={sqftMin}
          onChange={(e) =>
            dispatch({
              type: "SET_SQFT",
              payload: {
                min: Math.min(+e.target.value, sqftMax),
                max: sqftMax,
              },
            })
          }
        />
        <span className="opacity-70 text-xs">min {sqftMin}</span>
        <input
          type="range"
          min={350}
          max={5500}
          step={50}
          value={sqftMax}
          onChange={(e) =>
            dispatch({
              type: "SET_SQFT",
              payload: {
                min: sqftMin,
                max: Math.max(+e.target.value, sqftMin),
              },
            })
          }
        />
        <span className="opacity-70 text-xs">max {sqftMax}</span>
      </div>
    </SelectorShell>
  );
}

export default SqrtRangeSelector;

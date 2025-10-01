import SelectorShell from "./SelectorShell";
import { useFilters } from "../../context/FilterContext";

function SqrtRangeSelector() {
  const { dispatch, sqftMin, sqftMax } = useFilters();

  return (
    <SelectorShell type="Sqrf" className="px-4 py-6 sm:py-4 gap-6 text-sm">
      <div className="flex flex-col gap-6 w-full md:flex-row">
        <div className="flex items-center gap-3 sm:gap-1 w-full">
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
            className="flex-1 w-full accent-blue-500"
          />
          <span className="opacity-70 text-xs min-w-[70px] text-right">
            min {sqftMin}
          </span>
        </div>

        <div className="flex items-center gap-3 sm:gap-1 w-full">
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
            className="flex-1 w-full accent-blue-500"
          />
          <span className="opacity-70 text-xs min-w-[70px] text-right">
            max {sqftMax}
          </span>
        </div>
      </div>
    </SelectorShell>
  );
}

export default SqrtRangeSelector;

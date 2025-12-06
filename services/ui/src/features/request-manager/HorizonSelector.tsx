import SelectorShell from "./SelectorShell";
import { useFilters } from "../../context/FilterContext";

function HorizonSelector() {
  const horizons = ["1Y", "2Y", "5Y"];
  const { dispatch, horizon } = useFilters();

  return (
    <SelectorShell type="Horizon" className="px-4">
      <div className="flex rounded-xl overflow-hidden border w-[70%] sm:w-full ml-auto cursor-pointer border-selector-border bg-selector-bg">
        {horizons.map((h) => (
          <button
            key={h}
            onClick={() => dispatch({ type: "SET_HORIZON", payload: h })}
            className={`px-3 py-1.5 text-sm font-medium transition-all w-full  ${
              horizon === h
                ? "text-selector-btn-active-text"
                : "text-selector-btn-inactive-text"
            }`}
            style={{
              background:
                horizon === h
                  ? "var(--color-selector-btn-active-bg)"
                  : "var(--color-selector-btn-inactive-bg)",
            }}
            onMouseEnter={(e) => {
              if (horizon !== h)
                e.currentTarget.style.backgroundColor =
                  "var(--color-selector-btn-inactive-hover-bg)";
            }}
            onMouseLeave={(e) => {
              if (horizon !== h)
                e.currentTarget.style.backgroundColor =
                  "var(--color-selector-btn-inactive-bg)";
            }}
          >
            {h}
          </button>
        ))}
      </div>
    </SelectorShell>
  );
}

export default HorizonSelector;

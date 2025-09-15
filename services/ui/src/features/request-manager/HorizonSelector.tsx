import { useState } from "react";
import SelectorShell from "./SelectorShell";

function HorizonSelector() {
  const [horizon, setHorizon] = useState("5Y");
  const horizons = ["1Y", "2Y", "5Y", "10Y"];

  return (
    <SelectorShell type="Horizon" className="px-4">
      <div className="flex rounded-xl overflow-hidden border border-neutral-700">
        {horizons.map((h) => (
          <button
            key={h}
            onClick={() => setHorizon(h)}
            className={`px-3 py-1.5 text-sm transition-colors ${
              horizon === h
                ? "bg-neutral-200 text-neutral-900"
                : "bg-neutral-900 hover:bg-neutral-800 text-neutral-100"
            }`}
          >
            {h}
          </button>
        ))}
      </div>
    </SelectorShell>
  );
}

export default HorizonSelector;

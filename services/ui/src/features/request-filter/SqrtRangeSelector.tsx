import { useState } from "react";
import SelectorShell from "./SelectorShell";

function SqrtRangeSelector() {
  const [sqftMin, setSqftMin] = useState(500);
  const [sqftMax, setSqftMax] = useState(2500);

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
          onChange={(e) => setSqftMin(Math.min(+e.target.value, sqftMax))}
        />
        <span className="opacity-70 text-xs">min {sqftMin}</span>
        <input
          type="range"
          min={350}
          max={5500}
          step={50}
          value={sqftMax}
          onChange={(e) => setSqftMax(Math.max(+e.target.value, sqftMin))}
        />
        <span className="opacity-70 text-xs">max {sqftMax}</span>
      </div>
    </SelectorShell>
  );
}

export default SqrtRangeSelector;

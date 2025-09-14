import { useState } from "react";
import SelectorShell from "./SelectorShell";

function YeatBuiltSelector() {
  const [yearBuilt, setYearBuilt] = useState("any");

  return (
    <SelectorShell type="Year Built" className="px-4">
      <select
        value={yearBuilt}
        onChange={(e) => setYearBuilt(e.target.value)}
        className="bg-transparent focus:outline-none"
      >
        <option value="any" className="bg-neutral-900">
          Any
        </option>
        <option value="2000+" className="bg-neutral-900">
          2000+
        </option>
        <option value="2010+" className="bg-neutral-900">
          2010+
        </option>
        <option value="2020+" className="bg-neutral-900">
          2020+
        </option>
      </select>
    </SelectorShell>
  );
}

export default YeatBuiltSelector;

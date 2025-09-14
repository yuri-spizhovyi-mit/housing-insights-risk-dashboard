import { useState } from "react";
import SelectorShell from "./SelectorShell";
function BathsSelector() {
  const [baths, setBaths] = useState("any");

  return (
    <SelectorShell type="Baths" className="px-4">
      <select
        value={baths}
        onChange={(e) => setBaths(e.target.value)}
        className="bg-transparent focus:outline-none"
      >
        <option value="any" className="bg-neutral-900">
          Any
        </option>
        <option value="1" className="bg-neutral-900">
          1
        </option>
        <option value="2" className="bg-neutral-900">
          2
        </option>
        <option value="3+" className="bg-neutral-900">
          3+
        </option>
      </select>
    </SelectorShell>
  );
}

export default BathsSelector;

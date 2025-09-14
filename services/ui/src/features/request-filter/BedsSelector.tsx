import { useState } from "react";
import SelectorShell from "./SelectorShell";

function BedsSelector() {
  const [beds, setBeds] = useState("any");
  return (
    <SelectorShell type="Beds" className="px-6">
      <select
        value={beds}
        onChange={(e) => setBeds(e.target.value)}
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

export default BedsSelector;

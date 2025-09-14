import { useState } from "react";
import SelectorShell from "./SelectorShell";

function PropertyTypeSelector() {
  const [propertyType, setPropertyType] = useState("Condo");
  const propertyTypes = ["Condo", "House", "Town House", "Apartment"];

  return (
    <SelectorShell type="Type" className="px-4">
      <select
        value={propertyType}
        onChange={(e) => setPropertyType(e.target.value)}
        className="bg-transparent focus:outline-none px-1"
      >
        {propertyTypes.map((t) => (
          <option key={t} value={t} className="bg-neutral-900">
            {t}
          </option>
        ))}
      </select>
    </SelectorShell>
  );
}

export default PropertyTypeSelector;

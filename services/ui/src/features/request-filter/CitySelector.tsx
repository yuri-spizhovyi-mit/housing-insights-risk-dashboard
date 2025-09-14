import { MapPin } from "lucide-react";
import { useState } from "react";
import SelectorShell from "./SelectorShell";

function CitySelector() {
  const [city, setCity] = useState("Kelowna");
  const cities = ["Kelowna", "Vancouver", "Toronto"];

  return (
    <SelectorShell
      leftIcon={<MapPin className="size-4 opacity-70" />}
      className="px-4"
      type="City"
    >
      <select
        value={city}
        onChange={(e) => setCity(e.target.value)}
        className="bg-transparent focus:outline-none px-1"
      >
        {cities.map((c) => (
          <option key={c} value={c} className="bg-neutral-900">
            {c}
          </option>
        ))}
      </select>
    </SelectorShell>
  );
}

export default CitySelector;

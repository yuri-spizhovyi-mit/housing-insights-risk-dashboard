import Frame from "../../ui/Frame";

function WireframeNodes() {
  return (
    <Frame className="col-span-12">
      <h3 className="font-semibold mb-6 text-4xl">Wireframe Notes</h3>
      <ul className="list-disc pl-5 text-sm space-y-1 opacity-80">
        <li>
          Filters map to DB: bedrooms, bathrooms, area_sqft, year_built;
          property type maps to one-hot columns.
        </li>
        <li>
          Interpret UI values server-side: beds {">= 3"} when "3+", baths
          similarly; sqft uses [min, max].
        </li>
        <li>
          Horizon anchors at *today* and projects forward: 1Y (monthly), 2Y
          (every 2nd month), 5Y (every 6th month), 10Y (yearly).
        </li>
        <li>
          Charts show placeholder series; replace with real JSON from Spring →
          FastAPI.
        </li>
        <li>
          PDF button is non-functional; FE to call backend report endpoint or
          client PDF.
        </li>
        <li>
          Keep layout responsive (12-col grid). Mobile: stack cards vertically.
        </li>
      </ul>
    </Frame>
  );
}

export default WireframeNodes;

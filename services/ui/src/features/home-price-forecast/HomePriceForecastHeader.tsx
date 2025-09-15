import { Home } from "lucide-react";

function HomePriceForecastHeader() {
  return (
    <div className="flex items-center justify-between mb-9">
      <h2 className="font-semibold flex items-center gap-2">
        <Home className="size-5 opacity-80" /> Home Price Forecast
      </h2>
      <span className="text-xs opacity-60">
        prophet-like · 80/95% bands (stub)
      </span>
    </div>
  );
}

export default HomePriceForecastHeader;

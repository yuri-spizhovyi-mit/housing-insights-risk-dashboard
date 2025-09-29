import { LineChartIcon } from "lucide-react";

function RentForecastHeader() {
  return (
    <div className="flex items-center justify-between mb-9">
      <h2 className="font-semibold flex items-center gap-2">
        <LineChartIcon className="size-6" /> Rent Price Forecast
      </h2>
      <span className="text-xs opacity-60">baseline (stub)</span>
    </div>
  );
}

export default RentForecastHeader;

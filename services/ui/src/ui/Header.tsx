import { LineChartIcon } from "lucide-react";
import DownloadPdf from "./DownloadPdf";

function Header() {
  return (
    <header className="text-neutral-50 flex flex-col items-start gap-5.5 md:flex-row md:items-center justify-between px-6 py-4 border-b border-neutral-800 bg-neutral-900/60 backdrop-blur">
      <div className="flex items-center gap-3">
        <LineChartIcon className="size-6" />
        <h1 className="text-md sm:text-xl font-semibold tracking-tight">
          Housing Insights & Risk Forecast
        </h1>
      </div>

      <DownloadPdf />
    </header>
  );
}

export default Header;

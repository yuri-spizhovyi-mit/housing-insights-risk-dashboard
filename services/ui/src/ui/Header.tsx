import { LineChartIcon } from "lucide-react";
import DownloadPdf from "./DownloadPdf";
import ToggleButton from "./ToggleButton";

function Header() {
  return (
    <header className="flex flex-col md:flex-row items-start md:items-center justify-between px-6 py-4 gap-5.5 border-b border-neutral-800 bg-header-bg backdrop-blur text-primary transition-colors duration-500">
      <div className="flex items-center gap-3">
        <LineChartIcon className="size-6" />
        <h1 className="text-md sm:text-xl font-semibold tracking-tight">
          Housing Insights & Risk Forecast
        </h1>
      </div>

      <div className="flex flex-row-reverse gap-4 items-center sm:gap-8 sm:flex-row">
        <ToggleButton />
        <DownloadPdf />
      </div>
    </header>
  );
}

export default Header;

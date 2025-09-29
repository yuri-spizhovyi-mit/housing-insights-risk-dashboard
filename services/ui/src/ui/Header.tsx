import { Download, LineChartIcon } from "lucide-react";
import Button from "./Button";

function Header() {
  return (
    <header className="text-neutral-50 flex flex-col items-start gap-5.5 md:flex-row md:items-center justify-between px-6 py-4 border-b border-neutral-800 bg-neutral-900/60 backdrop-blur">
      <div className="flex items-center gap-3">
        <LineChartIcon className="size-6" />
        <h1 className="text-xl font-semibold tracking-tight">
          Housing Insights & Risk Forecast
        </h1>
      </div>

      <Button
        leftIcon={<Download className="size-4" />}
        className="rounded-2xl border border-neutral-700 px-4 py-2 hover:bg-neutral-800"
      >
        Download PDF (stub)
      </Button>
    </header>
  );
}

export default Header;

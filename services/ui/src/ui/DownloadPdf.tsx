import { Download } from "lucide-react";
import Button from "./Button";
import { useFilters } from "../context/FilterContext";
import { downloadReport } from "../services/report";

function DownloadPdf() {
  const { city } = useFilters();

  return (
    <Button
      leftIcon={<Download className="size-4" />}
      className="rounded-2xl border border-neutral-700 px-4 py-2 hover:bg-surface-muted-bg sm:text-lg text-sm"
      onClick={() => downloadReport(city)}
    >
      Download PDF
    </Button>
  );
}

export default DownloadPdf;

import { AlertCircle } from "lucide-react";
import RiskGaugeHeader from "./RiskGaugeHeader";
import Frame from "../../ui/Frame";
import { useRiskGauge } from "./useRiskGauge";
import Message from "../../ui/Message";
import { useFilters } from "../../context/FilterContext";
import { BreakdownList } from "./BreakdownList";
import RiskGaugeChart from "./RiskGaugeChart";

function RiskGauge() {
  const { city } = useFilters();
  const { risk, error, isFetching } = useRiskGauge(city);
  const riskScore = risk?.score ?? 0;

  return (
    <Frame className="col-span-12 lg:col-span-4 flex flex-col">
      <RiskGaugeHeader />

      {error ? (
        <Message
          type={error.type}
          message={error.message}
          details={error.details}
        />
      ) : isFetching ? (
        <p className="text-white">Fetching data..</p>
      ) : (
        <div className="flex gap-4 items-center">
          <RiskGaugeChart riskScore={riskScore} />
          <BreakdownList breakdown={risk?.breakdown} />
        </div>
      )}
      <div className="mt-auto text-xs flex items-start gap-2 opacity-70">
        <AlertCircle className="size-4" />
        <p>
          Interpretation: 0=low risk, 100=high risk. Composite for illustration.
        </p>
      </div>
    </Frame>
  );
}

export default RiskGauge;

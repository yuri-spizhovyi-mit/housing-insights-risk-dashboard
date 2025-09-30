import RiskGaugeHeader from "./RiskGaugeHeader";
import Frame from "../../ui/Frame";
import Message from "../../ui/Message";
import RiskGaugeChart from "./RiskGaugeChart";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";

import { AlertCircle } from "lucide-react";
import { useRiskGauge } from "./useRiskGauge";
import { BreakdownList } from "./BreakdownList";
import { useFilters } from "../../context/FilterContext";

function RiskGauge() {
  const { city } = useFilters();
  const { risk, error, isFetching } = useRiskGauge(city);
  const riskScore = risk?.score ?? 0;

  return (
    <Frame className="col-span-12 lg:col-span-4 flex flex-col">
      {isFetching ? (
        <Skeleton
          variant="rounded"
          width="100%"
          height={30}
          animation="wave"
          className="mb-9"
        />
      ) : (
        <RiskGaugeHeader />
      )}

      <div className="min-h-64 h-full mb-4 flex items-center">
        {isFetching ? (
          <div className="flex gap-8 sm:gap-4 mb-9 flex-col sm:flex-row flex-wrap items-start sm:items-center w-full">
            <div className="flex-[0.5] flex items-center justify-center w-full">
              <Skeleton
                variant="circular"
                width={140}
                height={140}
                animation="wave"
              />
            </div>

            <Stack className="flex-1 flex flex-col gap-6 w-full">
              <Skeleton variant="rounded" height={28} animation="wave" />
              <Skeleton variant="rounded" height={28} animation="wave" />
              <Skeleton variant="rounded" height={28} animation="wave" />
            </Stack>
          </div>
        ) : error ? (
          <Message
            type={error.type}
            message={error.message}
            details={error.details}
          />
        ) : (
          <div className="flex gap-4 items-center mb-9 flex-col sm:flex-row w-full">
            <RiskGaugeChart riskScore={riskScore} />
            <BreakdownList breakdown={risk?.breakdown} />
          </div>
        )}
      </div>

      <div className="mt-auto text-xs flex items-start gap-2 opacity-70">
        {isFetching ? (
          <Skeleton
            variant="rounded"
            width="100%"
            height={20}
            animation="wave"
            className="mt-auto"
          />
        ) : (
          <>
            <AlertCircle className="size-4" />
            <p>
              Interpretation: 0=low risk, 100=high risk. Composite for
              illustration.
            </p>
          </>
        )}
      </div>
    </Frame>
  );
}

export default RiskGauge;

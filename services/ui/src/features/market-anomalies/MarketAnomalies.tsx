import { Activity } from "lucide-react";
import { useFilters } from "../../context/FilterContext";
import Skeleton from "@mui/material/Skeleton";
import Message from "../../ui/Message";
import Frame from "../../ui/Frame";
import { useMarketAnomalies } from "./useMarketAnomalies";
import MarketAnomaliesChart from "./MarketAnomaliesChart";

function MarketAnomalies() {
  const { city } = useFilters();
  const { marketAnomalies, error, isFetching } = useMarketAnomalies(
    city,
    "rent"
  );

  return (
    <Frame className="col-span-12 lg:col-span-8 opacity-100 flex flex-col">
      {isFetching ? (
        <Skeleton
          variant="rounded"
          width="100%"
          height={30}
          animation="wave"
          className="mb-9"
        />
      ) : (
        <Frame.Header
          leftIcon={<Activity className="size-5 opacity-80" />}
          title="Market Anomalies"
          details="Isonlation Forest (stub)"
        />
      )}

      <Frame.Body className="min-h-64 flex-1">
        {isFetching ? (
          <Skeleton
            variant="rounded"
            width="100%"
            height="100%"
            animation="wave"
          />
        ) : error ? (
          <Message
            type={error.type}
            message={error.message}
            details={error.details}
          />
        ) : (
          <MarketAnomaliesChart data={marketAnomalies?.signals} />
        )}
      </Frame.Body>
    </Frame>
  );
}

export default MarketAnomalies;

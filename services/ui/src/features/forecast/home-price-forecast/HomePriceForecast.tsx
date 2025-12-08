import Frame from "../../../ui/Frame";
import { useFilters } from "../../../context/FilterContext";
import Message from "../../../ui/Message";
import HomePriceForecastChart from "./HomePriceForecastChart";
import { useForecast } from "../useForecast";
import Skeleton from "@mui/material/Skeleton";
import { Home } from "lucide-react";
import { useMemo } from "react";

function HomePriceForecast() {
  const filters = useFilters();
  const { forecast, error, isFetching } = useForecast(filters, "price");
  const memoizedData = useMemo(() => forecast?.data, [forecast?.data]);

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
          leftIcon={<Home className="size-5 opacity-80" />}
          title="Home Price Forecast"
          details="prophet-like · 80/95% bands"
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
          <HomePriceForecastChart data={memoizedData} />
        )}
      </Frame.Body>
    </Frame>
  );
}

export default HomePriceForecast;

import Frame from "../../../ui/Frame";
import Message from "../../../ui/Message";
import RentForecastChart from "./RentForecastChart";
import Skeleton from "@mui/material/Skeleton";

import { useFilters } from "../../../context/FilterContext";
import { useForecast } from "../useForecast";
import { LineChartIcon } from "lucide-react";

function RentForecast() {
  const filters = useFilters();
  const { forecast, error, isFetching } = useForecast(filters, "rent");

  return (
    <Frame className="col-span-12 lg:col-span-8 flex flex-col">
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
          leftIcon={<LineChartIcon className="size-6" />}
          title="Rent Price Forecast"
          details="baseline (stub)"
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
          <RentForecastChart data={forecast?.data} />
        )}
      </Frame.Body>
    </Frame>
  );
}

export default RentForecast;

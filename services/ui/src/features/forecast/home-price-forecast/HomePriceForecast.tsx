import Frame from "../../../ui/Frame";
import HomePriceForecastHeader from "./HomePriceForecastHeader";
import { useFilters } from "../../../context/FilterContext";
import Message from "../../../ui/Message";
import HomePriceForecastChart from "./HomePriceForecastChart";
import { useForecast } from "../useForecast";
import Skeleton from "@mui/material/Skeleton";

function HomePriceForecast() {
  const filters = useFilters();
  const { forecast, error, isFetching } = useForecast(filters, "price");

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
        <HomePriceForecastHeader />
      )}

      <div className="h-64 flex-1">
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
          <HomePriceForecastChart data={forecast?.data} />
        )}
      </div>
    </Frame>
  );
}

export default HomePriceForecast;

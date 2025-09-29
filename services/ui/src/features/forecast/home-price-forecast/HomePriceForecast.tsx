import Frame from "../../../ui/Frame";
import HomePriceForecastHeader from "./HomePriceForecastHeader";
import { useFilters } from "../../../context/FilterContext";
import Message from "../../../ui/Message";
import HomePriceForecastChart from "./HomePriceForecastChart";
import { useForecast } from "../useForecast";

function HomePriceForecast() {
  const filters = useFilters();
  const { forecast, error, isFetching } = useForecast(filters, "price");

  return (
    <Frame className="col-span-12 lg:col-span-8 opacity-100">
      <HomePriceForecastHeader />

      <div className="h-64">
        {error ? (
          <Message
            type={error.type}
            message={error.message}
            details={error.details}
          />
        ) : isFetching ? (
          <p className="text-gray-400">Fetching forecast…</p>
        ) : (
          <HomePriceForecastChart data={forecast?.data} />
        )}
      </div>
    </Frame>
  );
}

export default HomePriceForecast;

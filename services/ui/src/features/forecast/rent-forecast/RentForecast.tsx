import Frame from "../../../ui/Frame";
import RentForecastHeader from "./RentForecastHeader";
import { useFilters } from "../../../context/FilterContext";
import Message from "../../../ui/Message";
import RentForecastChart from "./RentForecastChart";
import { useForecast } from "../useForecast";

function RentForecast() {
  const filters = useFilters();
  const { forecast, error, isFetching } = useForecast(filters, "rent");

  return (
    <Frame className="col-span-12 lg:col-span-8">
      <RentForecastHeader />

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
          <RentForecastChart data={forecast?.data} />
        )}
      </div>
    </Frame>
  );
}

export default RentForecast;

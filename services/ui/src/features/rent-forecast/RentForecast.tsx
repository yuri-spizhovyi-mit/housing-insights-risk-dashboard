import Frame from "../../ui/Frame";
import RentForecastHeader from "./RentForecastHeader";
import RentForecastChart from "./RentForecastChart";

function RentForecast() {
  const staticData = [
    { date: "2025-01", value: 700 },
    { date: "2025-02", value: 710 },
    { date: "2025-03", value: 725 },
    { date: "2025-04", value: 730 },
    { date: "2025-05", value: 740 },
    { date: "2025-06", value: 755 },
    { date: "2025-07", value: 770 },
    { date: "2025-08", value: 785 },
    { date: "2025-09", value: 800 },
    { date: "2025-10", value: 810 },
  ];

  return (
    <Frame className="col-span-12 lg:col-span-8">
      <RentForecastHeader />
      <RentForecastChart data={staticData} />
    </Frame>
  );
}

export default RentForecast;

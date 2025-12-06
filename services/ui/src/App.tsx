import { useState } from "react";
import HomePriceForecast from "./features/forecast/home-price-forecast/HomePriceForecast";
import RentForecast from "./features/forecast/rent-forecast/RentForecast";
import MarketAnomalies from "./features/market-anomalies/MarketAnomalies";
import FilterManager from "./features/request-manager/FilterManager";
import RiskGauge from "./features/risk-gauge/RiskGauge";
import SentimentAndNews from "./features/sentiment-and-news/SentimentAndNews";
import UiOverview from "./features/static-boards/UiOverview";
import Dashboard from "./ui/Dashboard";
import Header from "./ui/Header";
import Main from "./ui/Main";
import Subheader from "./ui/Subheader";

function App() {
  const [forecastTrigger, setForecastTrigger] = useState(Date.now());
  return (
    <>
      <Subheader />
      <Header />
      <Main>
        <FilterManager setForecastTrigger={setForecastTrigger} />
        <Dashboard>
          <HomePriceForecast forecastTrigger={forecastTrigger} />
          <RiskGauge />
          <RentForecast forecastTrigger={forecastTrigger} />
          <SentimentAndNews />
          <MarketAnomalies />
          <UiOverview />
        </Dashboard>
      </Main>
    </>
  );
}

export default App;

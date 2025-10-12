import HomePriceForecast from "./features/forecast/home-price-forecast/HomePriceForecast";
import RentForecast from "./features/forecast/rent-forecast/RentForecast";
import MarketAnomalies from "./features/market-anomalies/MarketAnomalies";
import FilterManager from "./features/request-manager/FilterManager";
import RiskGauge from "./features/risk-gauge/RiskGauge";
import SentimentAndNews from "./features/sentiment-and-news/SentimentAndNews";
import UiOverview from "./features/static-boards/UiOverview";
import WireframeNotes from "./features/static-boards/WireframeNotes";
import { useSmoothScroll } from "./hooks/useSmoothScroll";
import Dashboard from "./ui/Dashboard";
import Header from "./ui/Header";
import Main from "./ui/Main";
import Subheader from "./ui/Subheader";

function App() {
  useSmoothScroll();

  return (
    <>
      <Subheader />
      <Header />
      <Main>
        <FilterManager />
        <Dashboard>
          <HomePriceForecast />
          <RiskGauge />
          <RentForecast />
          <SentimentAndNews />
          <MarketAnomalies />
          <UiOverview />
          <WireframeNotes />
        </Dashboard>
      </Main>
    </>
  );
}

export default App;

import HomePriceForecast from "./features/forecast/home-price-forecast/HomePriceForecast";
import RentForecast from "./features/forecast/rent-forecast/RentForecast";
import MarketAnomalies from "./features/market-anomalies/MarketAnomalies";
import HomePriceComparison from "./features/model-comparison/price-comparison-model/HomePriceComparison";
import RentComparison from "./features/model-comparison/rent-comparison-model/RentComparison";
import FilterManager from "./features/request-manager/FilterManager";
import RiskGauge from "./features/risk-gauge/RiskGauge";
import SentimentAndNews from "./features/sentiment-and-news/SentimentAndNews";
import ComparisonSummaryTable from "./features/static-boards/ComparisonSummaryTable";
import UiOverview from "./features/static-boards/UiOverview";
import Dashboard from "./ui/Dashboard";
import Header from "./ui/Header";
import Main from "./ui/Main";
import Subheader from "./ui/Subheader";

export default function App() {
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

          <HomePriceComparison />
          <ComparisonSummaryTable
            target="price"
            title="Home Price Model Summary"
          />

          <RentComparison />
          <ComparisonSummaryTable
            target="rent"
            title="Rent Price Model Summary"
          />
        </Dashboard>
      </Main>
    </>
  );
}

import HomePriceForecast from "./features/home-price-forecast/HomePriceForecast";
import RentForecast from "./features/rent-forecast/RentForecast";
import FilterManager from "./features/request-manager/FilterManager";
import RiskGauge from "./features/risk-gauge/RiskGauge";
import SentimentAndNews from "./features/sentiment-and-news/SentimentAndNews";
import ContainerGrid from "./ui/ContainerGrid";
import Header from "./ui/Header";
import Main from "./ui/Main";

function App() {
  return (
    <>
      <Header />
      <Main>
        <FilterManager />
        <ContainerGrid>
          <HomePriceForecast />
          <RiskGauge />
          <RentForecast />
          <SentimentAndNews />
        </ContainerGrid>
      </Main>
    </>
  );
}

export default App;

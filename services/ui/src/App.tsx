import HomePriceForecast from "./features/forecast/home-price-forecast/HomePriceForecast";
import RentForecast from "./features/forecast/rent-forecast/RentForecast";
import FilterManager from "./features/request-manager/FilterManager";
import RiskGauge from "./features/risk-gauge/RiskGauge";
import SentimentAndNews from "./features/sentiment-and-news/SentimentAndNews";
import WireframeNotes from "./features/wireframe-notes/WireframeNotes";
import { useSmoothScroll } from "./hooks/useSmoothScroll";
import Dashboard from "./ui/Dashboard";
import Footer from "./ui/Footer";
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
          <WireframeNotes />
        </Dashboard>
        <Footer />
      </Main>
    </>
  );
}

export default App;

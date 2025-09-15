import HomePriceForecast from "./features/home-price-forecast/HomePriceForecast";
import RentForecast from "./features/rent-forecast/RentForecast";
import FilterManager from "./features/request-manager/FilterManager";
import RiskGauge from "./features/risk-gauge/RiskGauge";
import SentimentAndNews from "./features/sentiment-and-news/SentimentAndNews";
import WireframeNotes from "./features/wireframe-notes/WireframeNotes";
import { useSmoothScroll } from "./hooks/useSmoothScroll";
import ContainerGrid from "./ui/ContainerGrid";
import Footer from "./ui/Footer";
import Header from "./ui/Header";
import Main from "./ui/Main";
import { ThemeProvider } from "./context/ThemeContext";
import Subheader from "./ui/Subheader";

function App() {
  useSmoothScroll();

  return (
    <ThemeProvider>
      <Subheader />
      <Header />
      <Main>
        <FilterManager />
        <ContainerGrid>
          <HomePriceForecast />
          <RiskGauge />
          <RentForecast />
          <SentimentAndNews />
          <WireframeNotes />
        </ContainerGrid>
        <Footer />
      </Main>
    </ThemeProvider>
  );
}

export default App;

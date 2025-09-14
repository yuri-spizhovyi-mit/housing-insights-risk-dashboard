// import HousingDashboardWireframe from "./Wireframe";

import FilterManager from "./features/request-filter/FilterManager";
// import FeaturesLayout from "./ui/FeaturesLayout";
import Header from "./ui/Header";
import Main from "./ui/Main";

function App() {
  return (
    <>
      <Header />
      <Main>
        <FilterManager />
        {/* <FeaturesLayout></FeaturesLayout> */}
      </Main>
    </>
  );
}

export default App;

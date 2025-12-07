import CitySelector from "./CitySelector";
import HorizonSelector from "./HorizonSelector";
import PropertyTypeSelector from "./PropertyTypeSelector.tsx";
import FilterContainer from "./FilterContainer.tsx";
import PredictTrigger from "./PredictTrigger.tsx";

function FilterManager() {
  return (
    <section className="px-6 pt-6">
      <FilterContainer>
        <CitySelector />
        <HorizonSelector />
        <PropertyTypeSelector />
        <PredictTrigger />
      </FilterContainer>
    </section>
  );
}

export default FilterManager;

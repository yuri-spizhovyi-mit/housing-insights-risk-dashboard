import { TrendingUp } from "lucide-react";
import Button from "../../ui/Button";
import BathsSelector from "./BathsSelector";
import BedsSelector from "./BedsSelector";
import CitySelector from "./CitySelector";
import HorizonSelector from "./HorizonSelector";
import PropertyTypeSelector from "./PropertyTypeSelector";
import SqrtRangeSelector from "./SqrtRangeSelector";
import YeatBuiltSelector from "./YeatBuiltSelector";
import { FilterProvider } from "../../context/FilterContext.tsx";
import FilterContainer from "./FilterContainer.tsx";

function FilterManager() {
  return (
    <section className="px-6 pt-6">
      <FilterProvider>
        <FilterContainer>
          <CitySelector />
          <HorizonSelector />
          <PropertyTypeSelector />
          <BedsSelector />
          <BathsSelector />
          <SqrtRangeSelector />
          <YeatBuiltSelector />

          <Button
            leftIcon={<TrendingUp className="w-4 h-4" />}
            className="ml-4 px-6 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold"
          >
            Predict
          </Button>
        </FilterContainer>
      </FilterProvider>
    </section>
  );
}

export default FilterManager;

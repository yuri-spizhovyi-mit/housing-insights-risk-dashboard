import SelectorShell from "./SelectorShell";
import { useFilters, type RequestModelType } from "../../context/FilterContext";
import FilterSelector from "./FilterSelector";

function PropertyTypeSelector() {
  const modelTypes = ["ARIMA", "LSTM", "prophet"];
  const { dispatch, modelType } = useFilters();

  return (
    <SelectorShell type="Model Type" className="px-4">
      <FilterSelector
        value={modelType}
        data={modelTypes}
        handleValueUpdate={(value: string) =>
          dispatch({
            type: "SET_MODEL_TYPE",
            payload: value.toLowerCase() as RequestModelType,
          })
        }
      />
    </SelectorShell>
  );
}

export default PropertyTypeSelector;

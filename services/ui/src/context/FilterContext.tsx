import { useReducer, type ReactNode } from "react";
import { FilterContext, initialState, reducer } from "./FilterContext";

export function FilterProvider({ children }: { children: ReactNode }) {
  const [{ city, horizon, modelType }, dispatch] = useReducer(
    reducer,
    initialState
  );

  return (
    <FilterContext.Provider
      value={{
        city,
        horizon,
        modelType,
        dispatch,
      }}
    >
      {children}
    </FilterContext.Provider>
  );
}

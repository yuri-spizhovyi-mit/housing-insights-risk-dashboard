import { useReducer, type ReactNode } from "react";
import { FilterContext, initialState, reducer } from "./FilterContext";

export function FilterProvider({ children }: { children: ReactNode }) {
  const [
    { city, horizon, propertyType, beds, baths, sqftMin, sqftMax, yearBuilt },
    dispatch,
  ] = useReducer(reducer, initialState);

  return (
    <FilterContext.Provider
      value={{
        city,
        horizon,
        propertyType,
        beds,
        baths,
        sqftMin,
        sqftMax,
        yearBuilt,
        dispatch,
      }}
    >
      {children}
    </FilterContext.Provider>
  );
}

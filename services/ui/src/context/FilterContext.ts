import { createContext, useContext, type Dispatch } from "react";

export type State = {
  city: string;
  horizon: string;
  propertyType: string;
  beds: string;
  baths: string;
  sqftMin: number;
  sqftMax: number;
  yearBuilt?: string;
};

export type FilterContextType = State & {
  target: string;
};

export type Action =
  | { type: "SET_CITY"; payload: string }
  | { type: "SET_HORIZON"; payload: string }
  | { type: "SET_PROPERTY_TYPE"; payload: string }
  | { type: "SET_BEDS"; payload: string }
  | { type: "SET_BATHS"; payload: string }
  | { type: "SET_SQFT"; payload: { min: number; max: number } }
  | { type: "SET_YEAR_BUILT"; payload: string }
  | { type: "RESET" };

export const initialState: State = {
  city: "Vancouver",
  horizon: "1Y",
  propertyType: "House",
  beds: "3",
  baths: "2",
  sqftMin: 1200,
  sqftMax: 3000,
  yearBuilt: "any",
};

export function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "SET_CITY":
      return { ...state, city: action.payload };
    case "SET_HORIZON":
      return { ...state, horizon: action.payload };
    case "SET_PROPERTY_TYPE":
      return { ...state, propertyType: action.payload };
    case "SET_BEDS":
      return { ...state, beds: action.payload };
    case "SET_BATHS":
      return { ...state, baths: action.payload };
    case "SET_SQFT":
      return {
        ...state,
        sqftMin: action.payload.min,
        sqftMax: action.payload.max,
      };
    case "SET_YEAR_BUILT":
      return { ...state, yearBuilt: action.payload };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

export const FilterContext = createContext<
  | (State & {
      dispatch: Dispatch<Action>;
    })
  | null
>(null);

export function useFilters() {
  const context = useContext(FilterContext);
  if (!context) {
    throw new Error("useFilters must be used within a FilterProvider");
  }
  return context;
}

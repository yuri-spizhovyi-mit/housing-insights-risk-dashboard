import { createContext, useContext, type Dispatch } from "react";

export type ModelType = "ARIMA" | "LSTM" | "prophet";
export type RequestModelType = "arima" | "lstm" | "prophet";

export type State = {
  city: string;
  horizon: string;
  modelType: RequestModelType;
};

export type FilterContextType = State & {
  target: string;
};

export type Action =
  | { type: "SET_CITY"; payload: string }
  | { type: "SET_HORIZON"; payload: string }
  | { type: "SET_MODEL_TYPE"; payload: RequestModelType }
  | { type: "RESET" };

export const initialState: State = {
  city: "Calgary",
  horizon: "1Y",
  modelType: "arima",
};

export function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "SET_CITY":
      return { ...state, city: action.payload };
    case "SET_HORIZON":
      return { ...state, horizon: action.payload };
    case "SET_MODEL_TYPE":
      return { ...state, modelType: action.payload };
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

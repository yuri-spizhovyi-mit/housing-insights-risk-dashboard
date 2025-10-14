import { useContext } from "react";
import { LenisContext } from "./LenisContextObject";

export function useLenis() {
  const context = useContext(LenisContext);

  if (!context) throw new Error("Please make sure ");

  return context;
}

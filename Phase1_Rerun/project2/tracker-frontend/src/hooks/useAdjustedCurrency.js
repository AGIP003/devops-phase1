import { useContext } from "react";

import { AdjustedCurrencyContext } from "../context/adjustedCurrencyContext";

export function useAdjustedCurrency() {
  const context = useContext(AdjustedCurrencyContext);
  if (!context) {
    throw new Error("useAdjustedCurrency must be used inside AdjustedCurrencyProvider");
  }
  return context;
}

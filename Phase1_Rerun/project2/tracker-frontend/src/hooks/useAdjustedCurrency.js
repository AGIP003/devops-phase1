import { useEffect, useMemo, useState } from "react";
import {
  formatAdjustedCurrency,
  getCurrencyByCode,
  getSavedCurrencyCode,
  saveCurrencyCode,
} from "../data/currencies";

export function useAdjustedCurrency() {
  const [currencyCode, setCurrencyCode] = useState(getSavedCurrencyCode);

  useEffect(() => {
    function handleCurrencyChange(event) {
      setCurrencyCode(event.detail || getSavedCurrencyCode());
    }

    window.addEventListener("adjusted-currency-change", handleCurrencyChange);
    return () => window.removeEventListener("adjusted-currency-change", handleCurrencyChange);
  }, []);

  return useMemo(() => {
    const currency = getCurrencyByCode(currencyCode);
    return {
      currency,
      currencyCode,
      setCurrencyCode: saveCurrencyCode,
      formatCurrency: (amount) => formatAdjustedCurrency(amount, currencyCode),
    };
  }, [currencyCode]);
}

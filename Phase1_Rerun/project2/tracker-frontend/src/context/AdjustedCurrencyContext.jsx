import { useCallback, useEffect, useMemo, useState } from "react";

import api from "../services/api";
import { AdjustedCurrencyContext } from "./adjustedCurrencyContext";
import {
  currencies,
  formatAdjustedCurrency,
  getCurrencyByCode,
  getSavedCurrencyCode,
  saveCurrencyCode,
} from "../data/currencies";


function validateRatesResponse(payload) {
  if (!payload || typeof payload !== "object" || !payload.rates) {
    throw new Error("Forex service returned an invalid response");
  }

  const normalizedRates = {};
  for (const currency of currencies) {
    const rate = Number(payload.rates[currency.code]);
    if (!Number.isFinite(rate) || rate <= 0) {
      throw new Error(`Forex rate for ${currency.code} is unavailable`);
    }
    normalizedRates[currency.code] = payload.rates[currency.code];
  }

  return normalizedRates;
}

export function AdjustedCurrencyProvider({ children }) {
  const [currencyCode, setCurrencyCode] = useState(getSavedCurrencyCode);
  const [rates, setRates] = useState({ KES: "1" });
  const [rateDate, setRateDate] = useState(null);
  const [fetchedAt, setFetchedAt] = useState(null);
  const [stale, setStale] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refreshRates = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/forex/rates");
      const normalizedRates = validateRatesResponse(response.data);

      setRates(normalizedRates);
      setRateDate(response.data.rateDate);
      setFetchedAt(response.data.fetchedAt);
      setStale(Boolean(response.data.stale));
    } catch (requestError) {
      setError(requestError.message || "Unable to load exchange rates");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshRates();
  }, [refreshRates]);

  useEffect(() => {
    function handleCurrencyChange(event) {
      setCurrencyCode(event.detail || getSavedCurrencyCode());
    }

    window.addEventListener("adjusted-currency-change", handleCurrencyChange);
    return () => window.removeEventListener("adjusted-currency-change", handleCurrencyChange);
  }, []);

  const value = useMemo(() => {
    const currency = getCurrencyByCode(currencyCode);
    return {
      currency,
      currencies,
      currencyCode,
      error,
      fetchedAt,
      formatCurrency: (amount) => formatAdjustedCurrency(amount, currencyCode, rates),
      loading,
      rateDate,
      rates,
      refreshRates,
      setCurrencyCode: saveCurrencyCode,
      stale,
    };
  }, [currencyCode, error, fetchedAt, loading, rateDate, rates, refreshRates, stale]);

  return (
    <AdjustedCurrencyContext.Provider value={value}>
      {children}
    </AdjustedCurrencyContext.Provider>
  );
}

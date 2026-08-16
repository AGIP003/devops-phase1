export const baseCurrency = "KES";

export const currencies = [
  { code: "KES", name: "Kenyan Shilling", symbol: "KSh" },
  { code: "USD", name: "US Dollar", symbol: "$" },
  { code: "EUR", name: "Euro", symbol: "€" },
  { code: "GBP", name: "British Pound", symbol: "£" },
  { code: "UGX", name: "Ugandan Shilling", symbol: "USh" },
  { code: "TZS", name: "Tanzanian Shilling", symbol: "TSh" },
];

export function getSavedCurrencyCode() {
  const savedCode = localStorage.getItem("adjustedCurrency");
  return currencies.some((currency) => currency.code === savedCode)
    ? savedCode
    : baseCurrency;
}

export function saveCurrencyCode(code) {
  if (!currencies.some((currency) => currency.code === code)) {
    return;
  }
  localStorage.setItem("adjustedCurrency", code);
  window.dispatchEvent(new CustomEvent("adjusted-currency-change", { detail: code }));
}

export function getCurrencyByCode(code) {
  return currencies.find((currency) => currency.code === code) || currencies[0];
}

export function convertFromKes(amount, currencyCode, rates) {
  const rate = Number(rates?.[currencyCode]);
  if (!Number.isFinite(rate) || rate <= 0) {
    return null;
  }
  return Number(amount || 0) * rate;
}

export function formatAdjustedCurrency(amount, currencyCode, rates) {
  const currency = getCurrencyByCode(currencyCode);
  const convertedAmount = convertFromKes(amount, currency.code, rates);
  if (convertedAmount === null) {
    return "Rate unavailable";
  }
  return new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency: currency.code,
    maximumFractionDigits: currency.code === "KES" ? 0 : 2,
  }).format(convertedAmount);
}

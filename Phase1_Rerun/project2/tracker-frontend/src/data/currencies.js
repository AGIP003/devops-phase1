export const baseCurrency = "KES";

export const currencies = [
  { code: "KES", name: "Kenyan Shilling", symbol: "KSh", rateFromKes: 1 },
  { code: "USD", name: "US Dollar", symbol: "$", rateFromKes: 0.0077 },
  { code: "EUR", name: "Euro", symbol: "€", rateFromKes: 0.0071 },
  { code: "GBP", name: "British Pound", symbol: "£", rateFromKes: 0.006 },
  { code: "UGX", name: "Ugandan Shilling", symbol: "USh", rateFromKes: 28.9 },
  { code: "TZS", name: "Tanzanian Shilling", symbol: "TSh", rateFromKes: 19.8 },
];

export function getSavedCurrencyCode() {
  return localStorage.getItem("adjustedCurrency") || baseCurrency;
}

export function saveCurrencyCode(code) {
  localStorage.setItem("adjustedCurrency", code);
  window.dispatchEvent(new CustomEvent("adjusted-currency-change", { detail: code }));
}

export function getCurrencyByCode(code) {
  return currencies.find((currency) => currency.code === code) || currencies[0];
}

export function convertFromKes(amount, currencyCode) {
  const currency = getCurrencyByCode(currencyCode);
  return Number(amount || 0) * currency.rateFromKes;
}

export function formatAdjustedCurrency(amount, currencyCode) {
  const currency = getCurrencyByCode(currencyCode);
  const convertedAmount = convertFromKes(amount, currency.code);
  return new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency: currency.code,
    maximumFractionDigits: currency.code === "KES" ? 0 : 2,
  }).format(convertedAmount);
}

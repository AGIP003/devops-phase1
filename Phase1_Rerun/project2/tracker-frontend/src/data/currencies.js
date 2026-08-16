export const baseCurrency = "KES";

export const currencies = [
  { code: "KES", name: "Kenyan Shilling", symbol: "KSh" },
  { code: "USD", name: "US Dollar", symbol: "$" },
  { code: "EUR", name: "Euro", symbol: "€" },
  { code: "GBP", name: "British Pound", symbol: "£" },
  { code: "UGX", name: "Ugandan Shilling", symbol: "USh" },
  { code: "TZS", name: "Tanzanian Shilling", symbol: "TSh" },
  { code: "AED", name: "UAE Dirham", symbol: "د.إ" },
  { code: "AUD", name: "Australian Dollar", symbol: "A$" },
  { code: "BIF", name: "Burundian Franc", symbol: "FBu" },
  { code: "CAD", name: "Canadian Dollar", symbol: "C$" },
  { code: "CHF", name: "Swiss Franc", symbol: "CHF" },
  { code: "CNY", name: "Chinese Yuan", symbol: "CN¥" },
  { code: "DKK", name: "Danish Krone", symbol: "kr" },
  { code: "HKD", name: "Hong Kong Dollar", symbol: "HK$" },
  { code: "INR", name: "Indian Rupee", symbol: "₹" },
  { code: "JPY", name: "Japanese Yen", symbol: "¥" },
  { code: "NOK", name: "Norwegian Krone", symbol: "kr" },
  { code: "RWF", name: "Rwandan Franc", symbol: "FRw" },
  { code: "SAR", name: "Saudi Riyal", symbol: "SAR" },
  { code: "SEK", name: "Swedish Krona", symbol: "kr" },
  { code: "SGD", name: "Singapore Dollar", symbol: "S$" },
  { code: "ZAR", name: "South African Rand", symbol: "R" },
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

export function convertCurrency(amount, fromCode, toCode, rates) {
  const fromRate = Number(rates?.[fromCode]);
  const toRate = Number(rates?.[toCode]);
  const numericAmount = Number(amount);

  if (
    !Number.isFinite(numericAmount)
    || !Number.isFinite(fromRate)
    || fromRate <= 0
    || !Number.isFinite(toRate)
    || toRate <= 0
  ) {
    return null;
  }

  return numericAmount * (toRate / fromRate);
}

export function formatCurrencyAmount(
  amount,
  currencyCode,
  maximumFractionDigits = currencyCode === "KES" ? 0 : 2,
) {
  if (!Number.isFinite(amount)) {
    return "Rate unavailable";
  }

  return new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits,
  }).format(amount);
}

export function formatAdjustedCurrency(amount, currencyCode, rates) {
  const currency = getCurrencyByCode(currencyCode);
  const convertedAmount = convertFromKes(amount, currency.code, rates);
  if (convertedAmount === null) {
    return "Rate unavailable";
  }
  return formatCurrencyAmount(convertedAmount, currency.code);
}

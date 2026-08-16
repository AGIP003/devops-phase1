import { useMemo, useState } from "react";
import {
  ArrowRightLeft,
  Calculator,
  Check,
  RefreshCw,
  Repeat2,
  Search,
} from "lucide-react";

import {
  convertCurrency,
  convertFromKes,
  formatCurrencyAmount,
  getCurrencyByCode,
} from "../data/currencies";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";


const sampleAmount = 10000;

function Forex() {
  const {
    currencies,
    currency,
    currencyCode,
    error,
    formatCurrency,
    loading,
    rateDate,
    rates,
    refreshRates,
    setCurrencyCode,
    stale,
  } = useAdjustedCurrency();
  const [amount, setAmount] = useState("10000");
  const [fromCode, setFromCode] = useState("KES");
  const [toCode, setToCode] = useState("USD");
  const [searchQuery, setSearchQuery] = useState("");

  const numericAmount = Number(amount);
  const amountIsValid = amount.trim() !== ""
    && Number.isFinite(numericAmount)
    && numericAmount >= 0;
  const convertedAmount = amountIsValid
    ? convertCurrency(numericAmount, fromCode, toCode, rates)
    : null;
  const unitRate = convertCurrency(1, fromCode, toCode, rates);
  const fromCurrency = getCurrencyByCode(fromCode);
  const toCurrency = getCurrencyByCode(toCode);

  const filteredCurrencies = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      return currencies;
    }
    return currencies.filter((item) => (
      item.code.toLowerCase().includes(query)
      || item.name.toLowerCase().includes(query)
    ));
  }, [currencies, searchQuery]);

  function swapCurrencies() {
    setFromCode(toCode);
    setToCode(fromCode);
  }

  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div>
          <span className={`coming-soon-pill ${stale ? "forex-status-stale" : ""}`}>
            {loading ? "Loading rates" : stale ? "Last known rates" : "Current CBK rates"}
          </span>
          <h1>Currency workspace</h1>
          <p>
            Convert currencies and choose how money appears across MoneyTiq.
            {rateDate ? ` CBK reference rates, dated ${rateDate}.` : ""}
          </p>
        </div>
        <button
          type="button"
          className="feature-primary-button"
          disabled={loading}
          onClick={refreshRates}
        >
          <RefreshCw size={17} aria-hidden="true" />
          {loading ? "Checking rates" : "Refresh"}
        </button>
      </div>

      {error && <p className="forex-error" role="alert">{error}</p>}
      {stale && (
        <p className="forex-stale-notice" role="status">
          The provider is temporarily unavailable. Showing the last validated rates.
        </p>
      )}

      <section className="forex-converter-card" aria-labelledby="currency-converter-title">
        <div className="forex-converter-heading">
          <span className="forex-converter-icon">
            <Calculator size={20} aria-hidden="true" />
          </span>
          <div>
            <span>Currency converter</span>
            <h2 id="currency-converter-title">Convert confidently with trusted rates</h2>
          </div>
        </div>

        <div className="forex-converter-controls">
          <label className="forex-converter-field">
            <span>Amount</span>
            <input
              type="number"
              min="0"
              step="any"
              inputMode="decimal"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
            />
          </label>

          <label className="forex-converter-field">
            <span>From</span>
            <select value={fromCode} onChange={(event) => setFromCode(event.target.value)}>
              {currencies.map((item) => (
                <option value={item.code} key={item.code}>
                  {item.code} — {item.name}
                </option>
              ))}
            </select>
          </label>

          <button
            type="button"
            className="forex-swap-button"
            aria-label="Swap currencies"
            onClick={swapCurrencies}
          >
            <Repeat2 size={20} aria-hidden="true" />
          </button>

          <label className="forex-converter-field">
            <span>To</span>
            <select value={toCode} onChange={(event) => setToCode(event.target.value)}>
              {currencies.map((item) => (
                <option value={item.code} key={item.code}>
                  {item.code} — {item.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="forex-converter-result" aria-live="polite">
          <div>
            <span>{fromCurrency.code} to {toCurrency.code}</span>
            <strong>
              {convertedAmount === null
                ? loading
                  ? "Waiting for rates…"
                  : amountIsValid
                    ? "Rate unavailable"
                    : "Enter a valid amount"
                : formatCurrencyAmount(convertedAmount, toCode, 4)}
            </strong>
          </div>
          <small>
            {unitRate === null
              ? "The selected reference rate is unavailable."
              : `1 ${fromCode} = ${unitRate.toLocaleString("en-KE", { maximumFractionDigits: 6 })} ${toCode}`}
          </small>
        </div>
      </section>

      <section className="forex-hero-card">
        <div>
          <span>Current display currency</span>
          <strong>{currency.code}</strong>
          <p>{currency.name}</p>
        </div>
        <div className="forex-conversion-preview">
          <small>KES {sampleAmount.toLocaleString("en-KE")} adjusted to</small>
          <strong>{formatCurrency(sampleAmount)}</strong>
        </div>
      </section>

      <section className="forex-market-section" aria-labelledby="display-currency-title">
        <div className="forex-market-heading">
          <div>
            <span>{currencies.length} CBK-supported currencies</span>
            <h2 id="display-currency-title">Choose your display currency</h2>
          </div>
          <label className="forex-search">
            <Search size={17} aria-hidden="true" />
            <span className="sr-only">Search currencies</span>
            <input
              type="search"
              placeholder="Search currency"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
            />
          </label>
        </div>

        <div className="forex-grid">
          {filteredCurrencies.map((item) => {
            const selected = item.code === currencyCode;
            const convertedRate = convertFromKes(1, item.code, rates);
            return (
              <button
                type="button"
                className={`forex-card ${selected ? "active" : ""}`}
                key={item.code}
                onClick={() => setCurrencyCode(item.code)}
              >
                <span className="forex-symbol">{item.symbol}</span>
                <div>
                  <strong>{item.code}</strong>
                  <small>{item.name}</small>
                </div>
                <div className="forex-rate">
                  <ArrowRightLeft size={15} aria-hidden="true" />
                  <span>
                    {convertedRate === null
                      ? "Unavailable"
                      : convertedRate.toLocaleString("en-KE", { maximumFractionDigits: 5 })}
                  </span>
                </div>
                {selected && <Check className="forex-check" size={18} aria-hidden="true" />}
              </button>
            );
          })}
        </div>

        {filteredCurrencies.length === 0 && (
          <p className="forex-empty-search">No supported currency matches that search.</p>
        )}
      </section>

      {!loading && !error && (
        <p className="forex-reference-note">
            Daily reference rates for display—not executable trading quotes.
        </p>
      )}
    </div>
  );
}

export default Forex;

import { ArrowRightLeft, Check, RefreshCw } from "lucide-react";
import { convertFromKes } from "../data/currencies";
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

  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div>
          <span className={`coming-soon-pill ${stale ? "forex-status-stale" : ""}`}>
            {loading ? "Loading rates" : stale ? "Last known rates" : "Current CBK rates"}
          </span>
          <h1>Adjusted Currency</h1>
          <p>
            Choose how money appears across the app.
            {rateDate ? ` CBK reference rates via Frankfurter, dated ${rateDate}.` : ""}
          </p>
        </div>
        <button
          type="button"
          className="feature-primary-button"
          disabled={loading}
          onClick={refreshRates}
        >
          <RefreshCw size={17} aria-hidden="true" />
          {loading ? "Checking rates" : "Check for updates"}
        </button>
      </div>

      {error && <p className="forex-error" role="alert">{error}</p>}
      {stale && (
        <p className="forex-stale-notice" role="status">
          The provider is temporarily unavailable. MoneyTiq is showing the last validated rates.
        </p>
      )}

      {!loading && !error && (
        <p className="forex-reference-note">
          Indicative daily reference rates for display—not executable trading quotes.
        </p>
      )}

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

      <section className="forex-grid">
        {currencies.map((item) => {
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
      </section>
    </div>
  );
}

export default Forex;

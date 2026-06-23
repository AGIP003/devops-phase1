import { ArrowRightLeft, Check, RefreshCw } from "lucide-react";
import { currencies, convertFromKes } from "../data/currencies";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";

const sampleAmount = 10000;

function Forex() {
  const { currency, currencyCode, setCurrencyCode, formatCurrency } = useAdjustedCurrency();

  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div>
          <span className="coming-soon-pill">Mock forex</span>
          <h1>Adjusted Currency</h1>
          <p>Choose how money appears across the app. Live rates will come from your scraper later.</p>
        </div>
        <button type="button" className="feature-primary-button" disabled>
          <RefreshCw size={17} aria-hidden="true" />
          Refresh rates
        </button>
      </div>

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
                <span>{convertFromKes(1, item.code).toLocaleString("en-KE", { maximumFractionDigits: 4 })}</span>
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

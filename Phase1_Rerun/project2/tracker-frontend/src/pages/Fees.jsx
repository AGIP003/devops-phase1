import { useEffect, useMemo, useState } from "react";
import {
  BadgePercent,
  Building2,
  Calculator,
  CircleAlert,
  ExternalLink,
  RefreshCw,
  ShieldCheck,
  Smartphone,
} from "lucide-react";

import api from "../services/api";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";

const PROVIDERS = {
  mpesa: { name: "M-PESA", tone: "#2f8f5b", icon: Smartphone },
  airtel_money: { name: "Airtel Money", tone: "#dc3d4b", icon: Smartphone },
  fuliza_mpesa: { name: "Fuliza M-PESA", tone: "#8b5cf6", icon: BadgePercent },
  bank: { name: "Bank", tone: "#3b82f6", icon: Building2 },
};

const dateFormatter = new Intl.DateTimeFormat("en-KE", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

function providerPresentation(provider) {
  return PROVIDERS[provider] || {
    name: provider?.replaceAll("_", " ") || "Other",
    tone: "#69746b",
    icon: BadgePercent,
  };
}

function Fees() {
  const { formatCurrency } = useAdjustedCurrency();
  const [summary, setSummary] = useState(null);
  const [catalog, setCatalog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [serviceKey, setServiceKey] = useState("airtel_money:other_network");
  const [amount, setAmount] = useState("1000");
  const [estimate, setEstimate] = useState(null);
  const [estimateError, setEstimateError] = useState("");
  const [estimating, setEstimating] = useState(false);
  const [expandedService, setExpandedService] = useState(null);

  async function loadFees() {
    setLoading(true);
    setError("");
    try {
      const [summaryResponse, catalogResponse] = await Promise.all([
        api.get("/fees/summary"),
        api.get("/fees/tariffs"),
      ]);
      setSummary(summaryResponse.data);
      setCatalog(catalogResponse.data);
    } catch (requestError) {
      setError(requestError.response?.data?.message || requestError.message || "Fee data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadFees();
  }, []);

  const highestProvider = summary?.providerTotals?.[0] || null;
  const maxProviderTotal = Math.max(
    ...(summary?.providerTotals || []).map((provider) => Number(provider.total)),
    1,
  );
  const selectedService = useMemo(() => {
    const [provider, service] = serviceKey.split(":");
    return { provider, service };
  }, [serviceKey]);
  const estimableServices = (catalog?.services || []).filter(
    (service) => service.estimationAvailable !== false,
  );
  const monitoredServices = (catalog?.services || []).filter(
    (service) => service.estimationAvailable === false,
  );
  const selectedServiceDefinition = (catalog?.services || []).find(
    (service) => `${service.provider}:${service.service}` === serviceKey,
  );
  const estimationAvailable = selectedServiceDefinition?.estimationAvailable !== false;

  async function calculateEstimate(event) {
    event.preventDefault();
    if (!estimationAvailable) return;
    setEstimating(true);
    setEstimateError("");
    setEstimate(null);
    try {
      const response = await api.post("/fees/estimate", {
        ...selectedService,
        amount,
      });
      setEstimate(response.data);
    } catch (requestError) {
      setEstimateError(requestError.response?.data?.message || requestError.message || "That fee could not be estimated.");
    } finally {
      setEstimating(false);
    }
  }

  if (loading && !summary) {
    return <div className="feature-state-card">Loading fee evidence…</div>;
  }

  if (error && !summary) {
    return (
      <div className="feature-state-card" role="alert">
        <CircleAlert aria-hidden="true" />
        <h1>Fees are unavailable</h1>
        <p>{error}</p>
        <button type="button" className="feature-primary-button" onClick={loadFees}>Try again</button>
      </div>
    );
  }

  return (
    <div className="feature-page fees-page">
      <header className="feature-page-header fees-page-header">
        <div>
          <h1>Transaction Fees</h1>
          <p>See confirmed charges separately from estimates, then check how much they add to your spending.</p>
        </div>
        <button type="button" className="analytics-refresh-button" onClick={loadFees} disabled={loading}>
          <RefreshCw size={16} className={loading ? "is-spinning" : ""} />
          Refresh
        </button>
      </header>

      {error && <div className="analytics-inline-error" role="alert">{error}</div>}

      <section className="feature-summary-grid fees-kpi-grid" aria-label="Fee totals">
        <article className="feature-summary-card fees-summary-card">
          <span>This week</span>
          <strong>{formatCurrency(summary?.totalWeek || 0)}</strong>
          <small>Calendar week from {summary?.period?.weekStart}</small>
        </article>
        <article className="feature-summary-card fees-summary-card">
          <span>This month</span>
          <strong>{formatCurrency(summary?.totalMonth || 0)}</strong>
          <small>{summary?.feeShareOfOutflows == null ? "No recorded outflow" : `${summary.feeShareOfOutflows}% of recorded outflow`}</small>
        </article>
        <article className="feature-summary-card fees-summary-card confirmed">
          <span>Confirmed</span>
          <strong>{formatCurrency(summary?.confirmedMonth || 0)}</strong>
          <small>Provider-reported or user-confirmed</small>
        </article>
        <article className="feature-summary-card fees-summary-card estimated">
          <span>Estimated</span>
          <strong>{formatCurrency(summary?.estimatedMonth || 0)}</strong>
          <small>{summary?.unknownFeeCount || 0} imported fees still unknown</small>
        </article>
      </section>

      <div className="fees-layout fees-live-layout">
        <section className="fees-breakdown-card">
          <div className="section-heading">
            <div>
              <h2><BadgePercent size={18} aria-hidden="true" /> Provider breakdown</h2>
              <p>Actual and clearly labelled estimated fees for this month.</p>
            </div>
          </div>
          <div className="fees-provider-list">
            {(summary?.providerTotals || []).length === 0 && (
              <div className="fees-empty-state">No fee-bearing records this month yet.</div>
            )}
            {(summary?.providerTotals || []).map((provider) => {
              const presentation = providerPresentation(provider.provider);
              const Icon = presentation.icon;
              return (
                <article className="fees-provider-row" key={provider.provider}>
                  <div className="fees-provider-icon" style={{ "--fee-tone": presentation.tone }} aria-hidden="true"><Icon size={18} /></div>
                  <div className="fees-provider-main">
                    <div><strong>{presentation.name}</strong><small>{provider.count} fee record{provider.count === 1 ? "" : "s"}</small></div>
                    <span>{formatCurrency(provider.total)}</span>
                  </div>
                  <div className="fees-provider-track" aria-hidden="true">
                    <span style={{ width: `${Math.max(5, Number(provider.total) / maxProviderTotal * 100)}%`, backgroundColor: presentation.tone }} />
                  </div>
                </article>
              );
            })}
          </div>
          {highestProvider && (
            <p className="fees-breakdown-note">
              Highest recorded provider: <strong>{providerPresentation(highestProvider.provider).name}</strong>. This describes your records, not the cheapest provider generally.
            </p>
          )}
        </section>

        <aside className="fees-side-stack">
          <section className="fees-calculator-card">
            <div className="fees-card-heading"><Calculator size={19} /><div><h2>Fee lookup</h2><p>Calculate a reviewed tariff or see how another charge is monitored.</p></div></div>
            <form className="fees-calculator-form" onSubmit={calculateEstimate}>
              <label><span>Fee type</span><select value={serviceKey} onChange={(event) => { setServiceKey(event.target.value); setEstimate(null); setEstimateError(""); }}>
                <optgroup label="Published estimates">
                  {estimableServices.map((service) => <option key={`${service.provider}:${service.service}`} value={`${service.provider}:${service.service}`}>{service.name}</option>)}
                </optgroup>
                <optgroup label="Track from your records">
                  {monitoredServices.map((service) => <option key={`${service.provider}:${service.service}`} value={`${service.provider}:${service.service}`}>{service.name}</option>)}
                </optgroup>
              </select></label>
              {estimationAvailable ? (
                <>
                  <label><span>Amount (KES)</span><input type="number" min="1" step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} /></label>
                  <button type="submit" className="feature-primary-button" disabled={estimating}>{estimating ? "Checking band…" : "Estimate fee"}</button>
                </>
              ) : (
                <div className="fees-monitor-only">
                  <ShieldCheck size={17} aria-hidden="true" />
                  <div>
                    <strong>Use the confirmed charge</strong>
                    <p>{selectedServiceDefinition?.helper}</p>
                    <small>{selectedServiceDefinition?.effectiveLabel}</small>
                    {selectedServiceDefinition?.source && (
                      <a href={selectedServiceDefinition.source} target="_blank" rel="noreferrer">
                        {selectedServiceDefinition.sourceLabel} <ExternalLink size={12} />
                      </a>
                    )}
                  </div>
                </div>
              )}
            </form>
            {estimateError && <p className="transaction-form-error" role="alert">{estimateError}</p>}
            {estimate && (
              <div className="fees-estimate-result">
                <span>Published-band estimate</span>
                <strong>{formatCurrency(estimate.estimatedFee)}</strong>
                <small>{estimate.serviceName} · amount {formatCurrency(estimate.amount)}</small>
                <a href={estimate.source} target="_blank" rel="noreferrer">{estimate.sourceLabel} <ExternalLink size={13} /></a>
                <p>{estimate.warning}</p>
              </div>
            )}
          </section>

          <section className="fees-insight-card">
            <div className="fees-insight-icon" aria-hidden="true"><ShieldCheck size={20} /></div>
            <div><h2>Evidence beats estimates</h2><p>Provider-message fees are preserved as confirmed. A tariff estimate remains visibly separate until you review it.</p></div>
          </section>
        </aside>
      </div>

      <section className="fees-tariff-section">
        <header><div><span>Fee coverage</span><h2>Compare and monitor fee types</h2><p>Published bands can be estimated; variable M-PESA, Fuliza and bank charges stay tied to provider evidence.</p></div><small>Catalog {catalog?.version}</small></header>
        <div className="fees-tariff-grid">
          {(catalog?.services || []).map((service) => {
            const presentation = providerPresentation(service.provider);
            const expanded = expandedService === `${service.provider}:${service.service}`;
            return (
              <article className="fees-tariff-card" style={{ "--fee-tone": presentation.tone }} key={`${service.provider}:${service.service}`}>
                <span>{presentation.name}</span>
                <h3>{service.name}</h3>
                <p>{service.helper}</p>
                <small>{service.effectiveLabel}</small>
                {service.estimationAvailable !== false ? (
                  <>
                    <button
                      type="button"
                      aria-expanded={expanded}
                      aria-label={`${expanded ? "Hide" : "View"} tariff bands for ${service.name}`}
                      onClick={() => setExpandedService(expanded ? null : `${service.provider}:${service.service}`)}
                    >
                      {expanded ? "Hide bands" : `View ${service.bands.length} bands`}
                    </button>
                    {expanded && <div className="fees-band-list">{service.bands.map((band) => <div key={band.upTo}><span>Up to KES {Number(band.upTo).toLocaleString("en-KE")}</span><strong>{formatCurrency(band.fee)}</strong></div>)}</div>}
                  </>
                ) : <span className="fees-monitor-badge">Tracked from your records</span>}
                <a href={service.source} target="_blank" rel="noreferrer">Official source <ExternalLink size={13} /></a>
              </article>
            );
          })}
        </div>
      </section>

      <div className="fees-lower-grid">
        <section className="fees-recent-card">
          <h2>Recent fee evidence</h2>
          <div className="fees-event-list">
            {(summary?.recentEvents || []).length === 0 && <div className="fees-empty-state">Import a provider message with a fee to see it here.</div>}
            {(summary?.recentEvents || []).map((event) => (
              <div className="fees-event-row" key={event.id}>
                <div><strong>{event.description}</strong><small>{providerPresentation(event.provider).name} · {dateFormatter.format(new Date(`${event.date}T00:00:00`))} · {event.source.replaceAll("_", " ")}</small></div>
                <span>{formatCurrency(event.fee)}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="fees-bank-card">
          <div className="fees-card-heading"><Building2 size={19} /><div><h2>Bank tariff references</h2><p>Not auto-estimated because account and channel rules differ.</p></div></div>
          <div className="fees-bank-list">{(catalog?.bankReferences || []).map((bank) => <a href={bank.source} target="_blank" rel="noreferrer" key={bank.name}><div><strong>{bank.name}</strong><small>{bank.sourceLabel}</small><p>{bank.note}</p></div><ExternalLink size={16} /></a>)}</div>
          <small className="fees-catalog-warning">{catalog?.warning}</small>
        </section>
      </div>
    </div>
  );
}

export default Fees;

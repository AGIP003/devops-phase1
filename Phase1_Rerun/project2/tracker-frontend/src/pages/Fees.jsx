import { BadgePercent, CreditCard, Lightbulb, Plus, Smartphone } from "lucide-react";
import { feeEvents, feeProviders, getFeeSummary, normalizeFeeProvider } from "../data/mockFinanceFeatures";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";

const dateFormatter = new Intl.DateTimeFormat("en-KE", {
  day: "2-digit",
  month: "short",
});

function Fees() {
  const { formatCurrency } = useAdjustedCurrency();
  const summary = getFeeSummary(feeEvents);
  const maxProviderTotal = Math.max(...summary.providerTotals.map((provider) => provider.total), 1);

  return (
    <div className="feature-page fees-page">
      <div className="feature-page-header">
        <div>
          <span className="coming-soon-pill">Estimated fees</span>
          <h1>Transaction Fees</h1>
          <p>See how much moving money is costing you across mobile money, banks, and checkout providers.</p>
        </div>
        <button type="button" className="feature-primary-button" disabled>
          <Plus size={17} aria-hidden="true" />
          Add tariff
        </button>
      </div>

      <section className="feature-summary-grid">
        <div className="feature-summary-card fees-summary-card">
          <span>This Week</span>
          <strong>{formatCurrency(summary.totalWeek)}</strong>
          <small>Estimated charges from recent activity</small>
        </div>
        <div className="feature-summary-card fees-summary-card">
          <span>This Month</span>
          <strong>{formatCurrency(summary.totalMonth)}</strong>
          <small>Money spent just moving money</small>
        </div>
        <div className="feature-summary-card fees-summary-card">
          <span>Highest Cost</span>
          <strong>{summary.highestProvider.name}</strong>
          <small>{formatCurrency(summary.highestProvider.total)} estimated</small>
        </div>
      </section>

      <div className="fees-layout">
        <section className="fees-breakdown-card">
          <div className="section-heading">
            <div>
              <h2>
                <BadgePercent size={18} aria-hidden="true" />
                Provider Breakdown
              </h2>
              <p>Mock tariff logic.</p>
            </div>
          </div>

          <div className="fees-provider-list">
            {summary.providerTotals.map((provider) => (
              <article className="fees-provider-row" key={provider.id}>
                <div
                  className="fees-provider-icon"
                  style={{ "--fee-tone": provider.tone }}
                  aria-hidden="true"
                >
                  {provider.id === "bank transfer" ? <CreditCard size={18} /> : <Smartphone size={18} />}
                </div>
                <div className="fees-provider-main">
                  <div>
                    <strong>{provider.name}</strong>
                    <small>{provider.helper}</small>
                  </div>
                  <span>{formatCurrency(provider.total)}</span>
                </div>
                <div className="fees-provider-track" aria-hidden="true">
                  <span
                    style={{
                      width: `${Math.max(6, Math.round((provider.total / maxProviderTotal) * 100))}%`,
                      backgroundColor: provider.tone,
                    }}
                  />
                </div>
              </article>
            ))}
          </div>
        </section>

        <aside className="fees-side-stack">
          <section className="fees-insight-card">
            <div className="fees-insight-icon" aria-hidden="true">
              <Lightbulb size={20} />
            </div>
            <div>
              <h2>Later AI Insight</h2>
              <p>
                Once backend data is set, AI can suggest cheaper rails, batch payments, or flag expensive transfer habits.
              </p>
            </div>
          </section>

          <section className="fees-recent-card">
            <h2>Recent Fee Events</h2>
            <div className="fees-event-list">
              {feeEvents.slice(0, 5).map((event) => {
                const provider = feeProviders.find((item) => item.id === normalizeFeeProvider(event.provider));
                return (
                  <div className="fees-event-row" key={event.id}>
                    <div>
                      <strong>{event.description}</strong>
                      <small>{provider?.name || event.provider} · {dateFormatter.format(new Date(event.date))}</small>
                    </div>
                    <span>{formatCurrency(event.fee)}</span>
                  </div>
                );
              })}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

export default Fees;

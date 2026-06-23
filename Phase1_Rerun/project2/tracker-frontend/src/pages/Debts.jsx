import { useId, useMemo, useState } from "react";
import { Landmark, Plus } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import {
  debts,
  getDebtChartData,
  getDebtProgress,
  getDebtSummary,
} from "../data/mockFinanceFeatures";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";

const dateFormatter = new Intl.DateTimeFormat("en-KE", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

const DEBT_COLORS = ["#6f7f3f", "#c2413b", "#2f8f5b", "#3b82f6", "#8b5cf6"];

const filterOptions = [
  { label: "All", value: "all" },
  { label: "I Owe", value: "i_owe" },
  { label: "Owed to Me", value: "owed_to_me" },
];

function DebtPulseLine({ progress }) {
  const gradientId = `debtPulse${useId().replace(/:/g, "")}`;
  return (
    <div className="debt-pulse-line" style={{ "--debt-progress": `${progress}%` }} aria-hidden="true">
      <svg viewBox="0 0 240 34" preserveAspectRatio="none">
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset={`${progress}%`} stopColor="#22c55e" />
            <stop offset={`${progress}%`} stopColor="#ef4444" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
        </defs>
        <path stroke={`url(#${gradientId})`} d="M2 20 H42 L51 10 L62 27 L75 14 L88 20 H126 L136 7 L150 29 L166 15 L180 20 H238" />
      </svg>
      <span className="debt-pulse-glow" />
    </div>
  );
}

function Debts() {
  const { formatCurrency } = useAdjustedCurrency();
  const currencyFormatter = { format: formatCurrency };
  const [activeFilter, setActiveFilter] = useState("all");
  const filteredDebts = useMemo(() => {
    if (activeFilter === "all") return debts;
    return debts.filter((debt) => debt.direction === activeFilter);
  }, [activeFilter]);
  const summary = getDebtSummary(debts);
  const chartData = getDebtChartData(filteredDebts);

  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div>
          <span className="coming-soon-pill">Frontend preview</span>
          <h1>Debts & Loans</h1>
          <p>Track what you owe, what people owe you, and repayment progress.</p>
        </div>
        <button type="button" className="feature-primary-button" disabled>
          <Plus size={17} aria-hidden="true" />
          Add debt
        </button>
      </div>

      <section className="feature-summary-grid">
        <div className="feature-summary-card debt-negative">
          <span>You Owe</span>
          <strong>{currencyFormatter.format(summary.youOwe)}</strong>
          <small>Banks, BNPL, SACCOs, people</small>
        </div>
        <div className="feature-summary-card debt-positive">
          <span>Owed to You</span>
          <strong>{currencyFormatter.format(summary.owedToYou)}</strong>
          <small>Money expected back</small>
        </div>
        <div className="feature-summary-card">
          <span>Net Position</span>
          <strong>{currencyFormatter.format(summary.netPosition)}</strong>
          <small>{summary.netPosition < 0 ? "More owed than receivable" : "Receivables ahead"}</small>
        </div>
      </section>

      <div className="debts-layout">
        <section className="debt-list-card">
          <div className="section-heading">
            <div>
              <h2>Debt List</h2>
              <p>Mock data until backend support is ready</p>
            </div>
          </div>

          <div className="feature-tabs" role="tablist" aria-label="Debt filter">
            {filterOptions.map((option) => (
              <button
                type="button"
                key={option.value}
                className={activeFilter === option.value ? "active" : ""}
                onClick={() => setActiveFilter(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>

          <div className="debt-list">
            {filteredDebts.map((debt) => {
              const progress = getDebtProgress(debt);
              return (
                <article className="debt-row-card" key={debt.id}>
                  <div className="debt-row-main">
                    <div className="debt-type-icon" aria-hidden="true">
                      <Landmark size={18} />
                    </div>
                    <div>
                      <h3>{debt.name}</h3>
                      <p>
                        {debt.type} · {debt.direction === "i_owe" ? "I owe" : "Owed to me"}
                      </p>
                    </div>
                  </div>

                  <div className="debt-row-amount">
                    <strong>{currencyFormatter.format(debt.balance)}</strong>
                    <small>Due {dateFormatter.format(new Date(debt.dueDate))}</small>
                  </div>

                  <div className="debt-progress-area">
                    <DebtPulseLine progress={progress} />
                    <small>{progress}% repaid · {debt.repaymentLabel}</small>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <aside className="chart-card debt-chart-card">
          <div className="chart-card-header">
            <h3>Loans Breakdown</h3>
            <span className="chart-card-kicker">Coming soon</span>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={58}
                outerRadius={105}
                paddingAngle={2}
                cornerRadius={6}
              >
                {chartData.map((_, index) => (
                  <Cell key={index} fill={DEBT_COLORS[index % DEBT_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => currencyFormatter.format(Number(value))} />
            </PieChart>
          </ResponsiveContainer>
          <div className="donut-legend">
            {chartData.map((item, index) => (
              <div className="donut-legend-item" key={item.name}>
                <span
                  className="donut-legend-dot"
                  style={{ backgroundColor: DEBT_COLORS[index % DEBT_COLORS.length] }}
                />
                <span className="donut-legend-name">{item.name}</span>
                <span className="donut-legend-percent">{currencyFormatter.format(item.value)}</span>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}

export default Debts;

import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, CalendarDays, CircleAlert, RefreshCw } from "lucide-react";
import api from "../services/api";
import EChart from "../components/analytics/EChart";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";

const PERIODS = [
  ["30-days", "30 days"],
  ["90-days", "90 days"],
  ["6-months", "6 months"],
  ["12-months", "12 months"],
  ["all", "All time"],
];

const CHART_COLORS = {
  income: "#7d8611",
  expenses: "#dd8d35",
  net: "#34495e",
  muted: "#69746b",
  grid: "#e3e8df",
};

function useCompactCalendar() {
  const [compact, setCompact] = useState(() => window.innerWidth <= 760);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return undefined;
    const media = window.matchMedia("(max-width: 760px)");
    const update = () => setCompact(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  return compact;
}

function shiftCalendar(anchor, amount) {
  const [year, month = "01"] = anchor.split("-").map(Number);
  const shifted = new Date(year, month - 1 + amount, 1);
  const nextYear = shifted.getFullYear();
  const nextMonth = String(shifted.getMonth() + 1).padStart(2, "0");
  return `${nextYear}-${nextMonth}`;
}

function compactCurrency(amount, currencyCode, rates) {
  const rate = Number(rates?.[currencyCode] || 1);
  return new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency: currencyCode || "KES",
    notation: "compact",
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  }).format(Number(amount) * rate);
}

function calendarMonthDays(monthKey, activity) {
  const [year, month] = monthKey.split("-").map(Number);
  const lastDay = new Date(year, month, 0).getDate();
  const activityByDate = new Map(activity.map((day) => [day.date, day]));

  return Array.from({ length: lastDay }, (_, index) => {
    const dayNumber = index + 1;
    const dateKey = `${year}-${String(month).padStart(2, "0")}-${String(dayNumber).padStart(2, "0")}`;
    const source = activityByDate.get(dateKey) || {
      date: dateKey,
      income: "0",
      expenses: "0",
      transactionCount: 0,
    };
    const income = Number(source.income || 0);
    const expenses = Number(source.expenses || 0);
    const direction = income > expenses
      ? "income"
      : expenses > income
        ? "expense"
        : "neutral";

    return {
      ...source,
      dayNumber,
      direction,
      dominant: Math.max(income, expenses),
    };
  });
}

function Analytics() {
  const { currencyCode, formatCurrency, rates } = useAdjustedCurrency();
  const compactCalendar = useCompactCalendar();
  const [period, setPeriod] = useState("12-months");
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [scenarioCategory, setScenarioCategory] = useState("");
  const [categoryReduction, setCategoryReduction] = useState(10);
  const [subscriptionReduction, setSubscriptionReduction] = useState(0);
  const [calendarAnchor, setCalendarAnchor] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  });

  const loadSummary = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/analytics/summary", { params: { period } });
      setSummary(response.data);
      setLastUpdated(new Date());
    } catch (requestError) {
      setError(requestError.message || "Analytics could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  useEffect(() => {
    if (!summary?.period?.end) return;
    setCalendarAnchor(summary.period.end.slice(0, 7));
  }, [summary?.period?.end]);

  useEffect(() => {
    const categories = summary?.expenseCategories || [];
    if (!categories.length) return;
    if (!categories.some((item) => item.category === scenarioCategory)) {
      setScenarioCategory(categories[0].category);
    }
  }, [scenarioCategory, summary?.expenseCategories]);

  const monthlyOption = useMemo(() => {
    const rows = summary?.monthlyTrend || [];
    return {
      aria: { enabled: true, description: "Monthly income, expenses and net cash flow" },
      color: [CHART_COLORS.income, CHART_COLORS.expenses, CHART_COLORS.net],
      tooltip: {
        trigger: "axis",
        valueFormatter: (value) => formatCurrency(value),
      },
      legend: { bottom: 0, textStyle: { color: CHART_COLORS.muted } },
      grid: { left: 18, right: 18, top: 18, bottom: 52, containLabel: true },
      xAxis: {
        type: "category",
        data: rows.map((row) => row.month),
        axisLabel: { color: CHART_COLORS.muted },
        axisLine: { lineStyle: { color: CHART_COLORS.grid } },
      },
      yAxis: {
        type: "value",
        axisLabel: {
          color: CHART_COLORS.muted,
          formatter: (value) => Intl.NumberFormat("en", { notation: "compact" }).format(value),
        },
        splitLine: { lineStyle: { color: CHART_COLORS.grid } },
      },
      series: [
        { name: "Income", type: "bar", data: rows.map((row) => Number(row.income)), barMaxWidth: 34 },
        { name: "Expenses", type: "bar", data: rows.map((row) => Number(row.expenses)), barMaxWidth: 34 },
        { name: "Net", type: "line", smooth: true, symbolSize: 7, data: rows.map((row) => Number(row.net)) },
      ],
    };
  }, [formatCurrency, summary?.monthlyTrend]);

  const categoryOption = useMemo(() => {
    const rows = [...(summary?.expenseCategories || [])].reverse();
    return {
      aria: { enabled: true, description: "Expense totals grouped by category" },
      color: [CHART_COLORS.expenses],
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        valueFormatter: (value) => formatCurrency(value),
      },
      grid: { left: 10, right: 24, top: 12, bottom: 12, containLabel: true },
      xAxis: {
        type: "value",
        axisLabel: { formatter: (value) => Intl.NumberFormat("en", { notation: "compact" }).format(value) },
        splitLine: { lineStyle: { color: CHART_COLORS.grid } },
      },
      yAxis: {
        type: "category",
        data: rows.map((row) => row.category),
        axisLabel: { color: CHART_COLORS.muted, width: 110, overflow: "truncate" },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [{
        name: "Expenses",
        type: "bar",
        data: rows.map((row) => Number(row.amount)),
        barMaxWidth: 24,
        itemStyle: { borderRadius: [0, 6, 6, 0] },
      }],
    };
  }, [formatCurrency, summary?.expenseCategories]);

  const commitmentOption = useMemo(() => {
    const commitments = summary?.commitments || {};
    const rows = [
      ["Bills", Number(commitments.monthlyBills || 0)],
      ["Subscriptions", Number(commitments.monthlySubscriptions || 0)],
      ["Debt payments", Number(commitments.monthlyDebtPayments || 0)],
      ["Goal contributions", Number(commitments.monthlyGoalContributions || 0)],
    ].sort((left, right) => left[1] - right[1]);
    return {
      aria: { enabled: true, description: "Estimated monthly financial commitments" },
      color: ["#9ea71c"],
      tooltip: { trigger: "axis", valueFormatter: (value) => formatCurrency(value) },
      grid: { left: 12, right: 28, top: 12, bottom: 12, containLabel: true },
      xAxis: {
        type: "value",
        axisLabel: { formatter: (value) => Intl.NumberFormat("en", { notation: "compact" }).format(value) },
        splitLine: { lineStyle: { color: CHART_COLORS.grid } },
      },
      yAxis: {
        type: "category",
        data: rows.map(([label]) => label),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: CHART_COLORS.muted },
      },
      series: [{
        name: "Monthly estimate",
        type: "bar",
        data: rows.map(([, value]) => value),
        barMaxWidth: 24,
        label: {
          show: true,
          position: "right",
          color: CHART_COLORS.muted,
          formatter: ({ value }) => Intl.NumberFormat("en", { notation: "compact" }).format(value),
        },
        itemStyle: { borderRadius: [0, 6, 6, 0] },
      }],
    };
  }, [formatCurrency, summary?.commitments]);

  const progressOption = useMemo(() => {
    const budget = summary?.budget || {};
    const goals = summary?.goals || {};
    const rows = [
      ["Budget used", Math.max(0, Number(budget.usedPercentage || 0))],
      ["Goals funded", Math.max(0, Number(goals.progressPercentage || 0))],
    ];
    return {
      aria: { enabled: true, description: "Budget use and savings goal progress percentages" },
      color: ["#9ea71c", "#e7ead4"],
      tooltip: { trigger: "axis", valueFormatter: (value) => `${Number(value).toFixed(1)}%` },
      grid: { left: 12, right: 24, top: 18, bottom: 12, containLabel: true },
      xAxis: {
        type: "value",
        max: Math.max(100, ...rows.map(([, value]) => value)),
        axisLabel: { formatter: "{value}%" },
        splitLine: { lineStyle: { color: CHART_COLORS.grid } },
      },
      yAxis: {
        type: "category",
        data: rows.map(([label]) => label),
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [{
        name: "Progress",
        type: "bar",
        data: rows.map(([, value]) => value),
        barWidth: 24,
        showBackground: true,
        backgroundStyle: { color: "#eef0e5", borderRadius: 8 },
        itemStyle: { borderRadius: 8 },
        label: { show: true, position: "insideLeft", color: "#ffffff", formatter: "{c}%" },
      }],
    };
  }, [summary?.budget, summary?.goals]);

  const debtOption = useMemo(() => {
    const debts = summary?.debts || {};
    const rows = [
      ["Active balance", Number(debts.activeBalance || 0)],
      ["Period repayments", Number(debts.periodRepayments || 0)],
      ["Recorded fees", Number(debts.periodFees || 0)],
    ];
    return {
      aria: { enabled: true, description: "Debt balance, repayments and recorded fees" },
      color: ["#34495e"],
      tooltip: { trigger: "axis", valueFormatter: (value) => formatCurrency(value) },
      grid: { left: 12, right: 28, top: 12, bottom: 12, containLabel: true },
      xAxis: {
        type: "value",
        axisLabel: { formatter: (value) => Intl.NumberFormat("en", { notation: "compact" }).format(value) },
        splitLine: { lineStyle: { color: CHART_COLORS.grid } },
      },
      yAxis: {
        type: "category",
        data: rows.map(([label]) => label),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: CHART_COLORS.muted },
      },
      series: [{
        name: "Debt position",
        type: "bar",
        data: rows.map(([, value]) => value),
        barMaxWidth: 22,
        itemStyle: { borderRadius: [0, 6, 6, 0] },
      }],
    };
  }, [formatCurrency, summary?.debts]);

  const scenario = useMemo(() => {
    const categories = summary?.expenseCategories || [];
    const selected = categories.find((item) => item.category === scenarioCategory);
    const start = summary?.period?.start ? new Date(`${summary.period.start}T00:00:00`) : null;
    const end = summary?.period?.end ? new Date(`${summary.period.end}T00:00:00`) : null;
    const coveredDays = start && end
      ? Math.max(Math.round((end - start) / 86400000) + 1, 1)
      : 30.4375;
    const monthlyCategory = Number(selected?.amount || 0) * 30.4375 / coveredDays;
    const categoryChange = monthlyCategory * categoryReduction / 100;
    const subscriptionChange = Number(summary?.commitments?.monthlySubscriptions || 0)
      * subscriptionReduction / 100;
    return {
      categoryChange,
      subscriptionChange,
      total: categoryChange + subscriptionChange,
    };
  }, [categoryReduction, scenarioCategory, subscriptionReduction, summary]);

  const scenarioOption = useMemo(() => ({
    aria: { enabled: true, description: "Illustrative monthly flexibility from the selected what-if changes" },
    color: ["#9ea71c"],
    tooltip: { trigger: "axis", valueFormatter: (value) => formatCurrency(value) },
    grid: { left: 12, right: 30, top: 12, bottom: 12, containLabel: true },
    xAxis: {
      type: "value",
      axisLabel: { formatter: (value) => Intl.NumberFormat("en", { notation: "compact" }).format(value) },
      splitLine: { lineStyle: { color: CHART_COLORS.grid } },
    },
    yAxis: {
      type: "category",
      data: [scenarioCategory || "Selected category", "Subscriptions"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: CHART_COLORS.muted, width: 120, overflow: "truncate" },
    },
    series: [{
      name: "Potential monthly flexibility",
      type: "bar",
      data: [scenario.categoryChange, scenario.subscriptionChange],
      barMaxWidth: 24,
      itemStyle: { borderRadius: [0, 6, 6, 0] },
      label: {
        show: true,
        position: "right",
        color: CHART_COLORS.muted,
        formatter: ({ value }) => Intl.NumberFormat("en", { notation: "compact" }).format(value),
      },
    }],
  }), [formatCurrency, scenario, scenarioCategory]);

  const calendarRange = calendarAnchor;
  const calendarOption = useMemo(() => {
    const activity = summary?.dailyActivity || [];
    const monthDays = calendarMonthDays(calendarRange, activity);
    const maximum = Math.max(...monthDays.map((day) => day.dominant), 1);
    return {
      aria: { enabled: true, description: "Monthly calendar showing the dominant income or expense amount for every day" },
      tooltip: {
        formatter: ({ data }) => {
          return [
            `<strong>${data.date}</strong>`,
            `Income: ${formatCurrency(data.income)}`,
            `Expenses: ${formatCurrency(data.expenses)}`,
            `Transactions: ${data.transactionCount}`,
          ].join("<br />");
        },
      },

       // ECharts requires visualMap for a heatmap series. It stays hidden because
      // direction-specific item styles and the visible legend carry the meaning.
      visualMap: {
        show: false,
        min: 0,
        max: maximum,
        dimension: 1,
      },

      calendar: {
        top: 36,
        left: compactCalendar ? 34 : 52,
        right: 16,
        bottom: 12,
        range: calendarRange,
        cellSize: ["auto", compactCalendar ? 58 : 74],
        splitLine: { show: false },
        itemStyle: { borderColor: "#ffffff", borderWidth: 3 },
        dayLabel: { firstDay: 1, nameMap: "en" },
        monthLabel: { show: false },
        yearLabel: { show: false },
      },
      series: [{
        type: "heatmap",
        coordinateSystem: "calendar",
        data: monthDays.map((day) => ({
          ...day,
          value: [day.date, day.dominant],
          itemStyle: {
            color: day.direction === "income"
              ? "#e4f3e8"
              : day.direction === "expense"
                ? "#fde8e5"
                : "#f5f6f1",
            borderColor: "#ffffff",
            borderWidth: 3,
          },
        })),
        label: {
          show: true,
          formatter: ({ data }) => {
            const amount = data.dominant > 0
              ? compactCurrency(data.dominant, currencyCode, rates)
              : "—";
            const sign = data.direction === "income" ? "+" : data.direction === "expense" ? "−" : "";
            return `{day|${data.dayNumber}}\n{${data.direction}|${sign}${amount}}`;
          },
          rich: {
            day: { color: "#59635c", fontSize: compactCalendar ? 10 : 12, fontWeight: 800, lineHeight: 20 },
            income: { color: "#237044", fontSize: compactCalendar ? 8 : 11, fontWeight: 900, lineHeight: 18 },
            expense: { color: "#a43e35", fontSize: compactCalendar ? 8 : 11, fontWeight: 900, lineHeight: 18 },
            neutral: { color: "#8a938c", fontSize: compactCalendar ? 8 : 11, fontWeight: 700, lineHeight: 18 },
          },
        },
      }],
    };
  }, [calendarRange, compactCalendar, currencyCode, formatCurrency, rates, summary?.dailyActivity]);

  if (loading && !summary) {
    return <div className="analytics-state">Loading your financial picture…</div>;
  }

  if (error && !summary) {
    return (
      <div className="analytics-state analytics-error" role="alert">
        <CircleAlert aria-hidden="true" />
        <h1>Analytics is unavailable</h1>
        <p>{error}</p>
        <button type="button" className="feature-primary-button" onClick={loadSummary}>Try again</button>
      </div>
    );
  }

  const cashFlow = summary?.cashFlow || {};
  const commitments = summary?.commitments || {};
  const hasTransactions = (summary?.monthlyTrend?.length || 0) > 0;
  const netCashFlow = Number(cashFlow.net || 0);
  const netInsight = netCashFlow < 0
    ? {
        severity: "high",
        title: "Outflows exceeded income",
        explanation: `${formatCurrency(Math.abs(netCashFlow))} more left than arrived in this period.`,
      }
    : netCashFlow > 0
      ? {
          severity: "low",
          title: "Cash flow remained positive",
          explanation: `${formatCurrency(netCashFlow)} remained after recorded expenses in this period.`,
        }
      : {
          severity: "low",
          title: "Cash flow balanced",
          explanation: "Recorded income and expenses produced no net difference in this period.",
        };
  const insightItems = [
    ...(summary?.adjustmentOpportunities || []),
    {
      type: "net_snapshot",
      ...netInsight,
    },
    {
      type: "commitment_snapshot",
      severity: Number(commitments.committedIncomePercentage || 0) >= 60 ? "high" : "low",
      title: "Monthly commitment pressure",
      explanation: commitments.committedIncomePercentage == null
        ? "Add income transactions to compare commitments with average monthly income."
        : `${commitments.committedIncomePercentage}% of average monthly income is assigned to bills, subscriptions, debts and goals.`,
    },
  ];

  return (
    <div className="feature-page analytics-page">
      <header className="feature-page-header analytics-header">
        <div>
          <span className="coming-soon-pill">Live financial analytics</span>
          <h1>Analytics</h1>
          <p>See what changed, useful insights, and where a review may help.</p>
        </div>
        <div className="analytics-periods" aria-label="Analytics period">
          {PERIODS.map(([value, label]) => (
            <button
              type="button"
              key={value}
              className={period === value ? "active" : ""}
              aria-pressed={period === value}
              onClick={() => setPeriod(value)}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      {error && (
        <div className="analytics-inline-error" role="alert">
          <CircleAlert size={17} aria-hidden="true" />
          Showing the last result. Refresh failed: {error}
          <button type="button" onClick={loadSummary}><RefreshCw size={15} /> Retry</button>
        </div>
      )}

      <section className="analytics-visual-grid">
        <article className="analytics-panel analytics-lead-chart">
          <header>
            <div><span>Money movement</span><h2>Cash-flow rhythm</h2><p>Monthly inflows and outflows; the line shows what remained.</p></div>
            <div className="analytics-chart-summary" aria-label="Cash-flow values">
              <span>Net <strong>{formatCurrency(cashFlow.net || 0)}</strong></span>
              <span>Saved <strong>{cashFlow.savingsRate == null ? "—" : `${cashFlow.savingsRate}%`}</strong></span>
            </div>
          </header>
          {hasTransactions
            ? <EChart option={monthlyOption} ariaLabel="Monthly income, expenses and net cash-flow chart" />
            : <div className="analytics-chart-empty"><CalendarDays size={22} /><span>No transaction movement in this period.</span></div>}
        </article>

        <article className="analytics-panel analytics-insight-panel">
          <header>
            <div><span>Fresh signals</span><h2>What deserves attention</h2><p>Recalculated for the selected period.</p></div>
            <button type="button" className="analytics-refresh-button" onClick={loadSummary} disabled={loading}>
              <RefreshCw size={15} className={loading ? "is-spinning" : ""} />
              Refresh
            </button>
          </header>
          <div className="analytics-opportunity-list">
            {insightItems.map((item) => (
              <div key={`${item.type}-${item.title}`} className={`severity-${item.severity}`}>
                <strong>{item.title}</strong>
                <p>{item.explanation}</p>
              </div>
            ))}
          </div>
          {lastUpdated && <small className="analytics-refresh-time">Updated {lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</small>}
        </article>
        <section className="analytics-panel analytics-calendar-panel">
            <header>
              <div><span>Daily rhythm</span><h2>Spending calendar</h2><p>Intensity shows which days carried the most expense activity.</p></div>
              <div className="calendar-controls">
                <button type="button" aria-label="Previous month" onClick={() => setCalendarAnchor((value) => shiftCalendar(value, -1))}><ArrowLeft size={16} /></button>
                <strong>{calendarRange}</strong>
                <button type="button" aria-label="Next month" onClick={() => setCalendarAnchor((value) => shiftCalendar(value, 1))}><ArrowRight size={16} /></button>
              </div>
            </header>
            <div className="analytics-calendar-legend" aria-label="Calendar color key">
              <span className="income">+ Income dominant</span>
              <span className="expense">− Expense dominant</span>
              <span className="neutral">— No movement or equal</span>
            </div>
            <EChart option={calendarOption} ariaLabel={`Daily income and expense calendar for ${calendarRange}`} className={compactCalendar ? "compact-calendar" : "month-calendar"} />
        </section>
        <article className="analytics-panel">
          <header><div><span>Spending mix</span><h2>Where money went</h2><p>Expense categories ranked by total.</p></div></header>
          {(summary?.expenseCategories || []).length
            ? <EChart option={categoryOption} ariaLabel="Horizontal bar chart of expenses by category" />
            : <div className="analytics-chart-empty"><span>No category spending to compare.</span></div>}
        </article>

        <article className="analytics-panel">
          <header><div><span>Fixed pressure</span><h2>Monthly commitments</h2><p>Bills, subscriptions, debt schedules and goal requirements.</p></div><strong className="analytics-panel-total">{formatCurrency(commitments.totalMonthlyCommitted || 0)}</strong></header>
          <EChart option={commitmentOption} ariaLabel="Horizontal bar chart of estimated monthly commitments" />
        </article>

        <article className="analytics-panel">
          <header><div><span>Plans</span><h2>Budget and goal progress</h2><p>Progress against the current plan, capped visually at the highest observed percentage.</p></div></header>
          <EChart option={progressOption} ariaLabel="Budget use and savings goal progress chart" />
        </article>

        <article className="analytics-panel">
          <header><div><span>Liabilities</span><h2>Debt position</h2><p>Current balance compared with activity in the selected period.</p></div></header>
          <EChart option={debtOption} ariaLabel="Debt balance, repayments and recorded fees chart" />
        </article>

        <section className="analytics-panel analytics-scenario-panel">
          <header>
            <div><span>What-if lab</span><h2>Explore your own adjustment</h2><p>Change assumptions to see an illustration. Nothing here is saved or applied to your finances.</p></div>
            <div className="scenario-result"><small>Potential monthly flexibility</small><strong>{formatCurrency(scenario.total)}</strong></div>
          </header>
          <div className="analytics-scenario-layout">
            <div className="scenario-controls">
              <label>
                <span>Category to explore</span>
                <select value={scenarioCategory} onChange={(event) => setScenarioCategory(event.target.value)}>
                  {(summary?.expenseCategories || []).map((item) => (
                    <option value={item.category} key={item.category}>{item.category}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>Try reducing that category <strong>{categoryReduction}%</strong></span>
                <input type="range" min="0" max="50" step="5" value={categoryReduction} onChange={(event) => setCategoryReduction(Number(event.target.value))} />
              </label>
              <label>
                <span>Try reducing subscriptions <strong>{subscriptionReduction}%</strong></span>
                <input type="range" min="0" max="100" step="10" value={subscriptionReduction} onChange={(event) => setSubscriptionReduction(Number(event.target.value))} />
              </label>
              <button type="button" className="scenario-reset" onClick={() => { setCategoryReduction(10); setSubscriptionReduction(0); }}>
                Reset assumptions
              </button>
            </div>
            <EChart option={scenarioOption} ariaLabel="What-if scenario monthly flexibility chart" className="scenario-chart" />
          </div>
          <small className="scenario-disclaimer">Illustration only: category spending is converted to a monthly average for the selected period. Actual savings depend on future behaviour and obligations.</small>
        </section>

      </section>

      <section className="analytics-method-note">
        <strong>How these figures are calculated</strong>
        <p>Actual cash flow comes from your non-deleted transactions. Commitments are monthly estimates from active bills, subscriptions, debt schedules and goal gaps. Recorded debt fees are shown separately and transaction fees remain unavailable until transactions store them explicitly. No AI generates these totals.</p>
      </section>
    </div>
  );
}

export default Analytics;

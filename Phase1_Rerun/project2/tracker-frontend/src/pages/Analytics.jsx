import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CalendarDays,
  CircleAlert,
  MessageCircle,
  MoveRight,
  RefreshCw,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
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

const SEARCH_PERIODS = [
  ["week", "Week"],
  ["month", "Month"],
  ["year", "Year"],
];

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

function readablePeriod(period) {
  const format = (value) => new Intl.DateTimeFormat("en-KE", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));

  if (!period?.end) return "Selected period";
  if (!period.start) return `All records through ${format(period.end)}`;
  return `${format(period.start)} – ${format(period.end)}`;
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
  const navigate = useNavigate();
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
  const [trendQuery, setTrendQuery] = useState("");
  const [trendPeriod, setTrendPeriod] = useState("month");
  const [trendMetric, setTrendMetric] = useState("amount");
  const [trend, setTrend] = useState(null);
  const [trendLoading, setTrendLoading] = useState(false);
  const [trendError, setTrendError] = useState("");
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiResult, setAiResult] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");
  const [weeklySummary, setWeeklySummary] = useState(null);
  const [weeklyLoading, setWeeklyLoading] = useState(false);
  const [dismissedInsights, setDismissedInsights] = useState(() => new Set());
  const [lastDismissedInsight, setLastDismissedInsight] = useState(null);

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
    setDismissedInsights(new Set());
    setLastDismissedInsight(null);
  }, [period]);

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

  const trendOption = useMemo(() => {
    const rows = trend?.series || [];
    const metricLabel = trendMetric === "count" ? "Times" : "Amount";
    return {
      aria: {
        enabled: true,
        description: `${metricLabel} matching ${trend?.query || "the search"} across the selected period`,
      },
      color: [CHART_COLORS.expenses],
      tooltip: {
        trigger: "axis",
        valueFormatter: (value) => trendMetric === "count" ? `${value} transactions` : formatCurrency(value),
      },
      grid: { left: 12, right: 20, top: 18, bottom: 42, containLabel: true },
      xAxis: {
        type: "category",
        data: rows.map((row) => row.bucket),
        axisLabel: { color: CHART_COLORS.muted, hideOverlap: true },
        axisLine: { lineStyle: { color: CHART_COLORS.grid } },
      },
      yAxis: {
        type: "value",
        minInterval: trendMetric === "count" ? 1 : 0,
        axisLabel: {
          formatter: (value) => trendMetric === "count"
            ? value
            : Intl.NumberFormat("en", { notation: "compact" }).format(value),
        },
        splitLine: { lineStyle: { color: CHART_COLORS.grid } },
      },
      series: [{
        name: metricLabel,
        type: "bar",
        data: rows.map((row) => trendMetric === "count" ? row.count : Number(row.amount)),
        barMaxWidth: 34,
        itemStyle: { borderRadius: [6, 6, 0, 0] },
      }],
    };
  }, [formatCurrency, trend, trendMetric]);

  const searchTrend = async (event) => {
    event.preventDefault();
    const query = trendQuery.trim();
    if (query.length < 2) {
      setTrendError("Enter at least two characters.");
      return;
    }
    setTrendLoading(true);
    setTrendError("");
    try {
      const response = await api.get("/analytics/description-trend", {
        params: { query, period: trendPeriod },
      });
      setTrend(response.data);
    } catch (requestError) {
      setTrendError(
        requestError.response?.data?.message
          || requestError.message
          || "That spending trend could not be loaded."
      );
    } finally {
      setTrendLoading(false);
    }
  };

  const askFinanceAssistant = async (event) => {
    event.preventDefault();
    const question = aiQuestion.trim();
    if (!question) return;
    setAiLoading(true);
    setAiError("");
    try {
      const response = await api.post("/ai/analytics/questions", { question });
      setAiResult(response.data);
    } catch (requestError) {
      setAiError(
        requestError.response?.data?.message
          || requestError.message
          || "The finance assistant is unavailable."
      );
    } finally {
      setAiLoading(false);
    }
  };

  const loadWeeklySummary = async () => {
    setWeeklyLoading(true);
    setAiError("");
    try {
      const response = await api.post("/ai/analytics/weekly-summary");
      setWeeklySummary(response.data.narrative);
    } catch (requestError) {
      setAiError(
        requestError.response?.data?.message
          || requestError.message
          || "The weekly review is unavailable."
      );
    } finally {
      setWeeklyLoading(false);
    }
  };

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
  const leadingCategory = summary?.expenseCategories?.[0];
  const insightPeriod = readablePeriod(summary?.period);
  const periodTransactionCount = (summary?.dailyActivity || []).reduce(
    (total, day) => total + Number(day.transactionCount || 0),
    0,
  );
  const hasCommitmentWarning = insightItems.some(
    (item) => item.type === "commitment_pressure",
  );
  const insightCards = insightItems
    .filter((item) => item.type !== "commitment_snapshot" || !hasCommitmentWarning)
    .map((item) => {
      if (item.type === "category_concentration") {
        const recordedExpenses = Number(cashFlow.recordedExpenses || 0);
        const categoryAmount = Number(leadingCategory?.amount || 0);
        const share = recordedExpenses > 0
          ? categoryAmount / recordedExpenses * 100
          : 0;
        return {
          ...item,
          title: `${leadingCategory?.category || "Your top category"} is your largest spending area`,
          label: "Data insight",
          metric: `${share.toFixed(0)}%`,
          supporting: `${formatCurrency(categoryAmount)} across ${leadingCategory?.transactionCount || 0} transaction${leadingCategory?.transactionCount === 1 ? "" : "s"}`,
          comparison: "Share of all recorded spending in this period",
          caveat: "Only transactions saved in Moneytiqx are included.",
          actionLabel: "See transactions",
          review: {
            category: leadingCategory?.category,
            from: summary?.period?.start,
            to: summary?.period?.end,
          },
          question: `How much did I spend on ${leadingCategory?.category || "my top category"} in this period, and where could I adjust?`,
        };
      }
      if (item.type === "debt_fees") {
        return {
          ...item,
          title: "Debt fees added to your repayments",
          label: "Data insight",
          metric: formatCurrency(summary?.debts?.periodFees || 0),
          supporting: "Recorded debt fees in the selected period",
          comparison: Number(summary?.debts?.periodRepayments || 0) > 0
            ? `${(Number(summary.debts.periodFees || 0) / Number(summary.debts.periodRepayments) * 100).toFixed(1)}% of recorded repayments`
            : "No repayment comparison is available yet",
          caveat: "This includes recorded debt fees, not unrecorded lender charges.",
          actionLabel: "Review debts",
          reviewPath: "/debts",
          question: "How much did debt fees cost me in this period?",
        };
      }
      if (item.type === "commitment_pressure" || item.type === "commitment_snapshot") {
        const percentage = commitments.committedIncomePercentage;
        return {
          ...item,
          title: percentage == null
            ? "Add income to measure monthly pressure"
            : Number(percentage) >= 60
              ? "Most monthly income is already spoken for"
              : "Part of your monthly income is already planned",
          label: "Data insight",
          metric: percentage == null ? "—" : `${percentage}%`,
          supporting: `${formatCurrency(commitments.totalMonthlyCommitted || 0)} planned each month`,
          comparison: "Compared with average monthly recorded income",
          caveat: "Planned amounts can differ from what is eventually paid.",
          actionLabel: "View breakdown",
          actionTarget: "analytics-commitments",
          question: "How much of my income is committed each month, and what contributes most?",
        };
      }
      if (item.type === "net_snapshot") {
        return {
          ...item,
          title: netCashFlow < 0
            ? "Spending ran ahead of income"
            : netCashFlow > 0
              ? "Income stayed ahead of spending"
              : "Income and spending balanced",
          label: "Data insight",
          metric: formatCurrency(Math.abs(netCashFlow)),
          supporting: `${periodTransactionCount} recorded transaction${periodTransactionCount === 1 ? "" : "s"} produced this result`,
          comparison: cashFlow.savingsRate == null
            ? "Add income to calculate the share that remained"
            : `${cashFlow.savingsRate}% of recorded income remained`,
          caveat: "This view cannot include cash activity you have not recorded.",
          actionLabel: "See transactions",
          review: {
            from: summary?.period?.start,
            to: summary?.period?.end,
          },
          question: "Explain my net cash flow for this period and show the main drivers.",
        };
      }
      return {
        ...item,
        label: "Data insight",
        metric: "Review",
        supporting: item.explanation,
        comparison: "A new signal was found in the selected period",
        caveat: "Check the underlying records before acting on this finding.",
        actionLabel: "See transactions",
        review: {
          from: summary?.period?.start,
          to: summary?.period?.end,
        },
        question: `Explain this finding: ${item.title}`,
      };
    });
  const visibleInsightCards = insightCards.filter(
    (card) => !dismissedInsights.has(card.type),
  );

  function reviewInsight(card) {
    if (card.reviewPath) {
      navigate(card.reviewPath);
      return;
    }
    if (card.review) {
      const params = new URLSearchParams();
      if (card.review.category) params.set("category", card.review.category);
      if (card.review.from) params.set("from", card.review.from);
      if (card.review.to) params.set("to", card.review.to);
      navigate(`/transactions?${params.toString()}`);
      return;
    }
    moveToInsightTarget(card);
  }

  function dismissInsight(card) {
    setDismissedInsights((current) => new Set(current).add(card.type));
    setLastDismissedInsight(card);
  }

  function undoDismissInsight() {
    if (!lastDismissedInsight) return;
    setDismissedInsights((current) => {
      const next = new Set(current);
      next.delete(lastDismissedInsight.type);
      return next;
    });
    setLastDismissedInsight(null);
  }

  function moveToInsightTarget(card) {
    if (card.type === "category_concentration" && leadingCategory?.category) {
      setScenarioCategory(leadingCategory.category);
    }
    document.getElementById(card.actionTarget)?.scrollIntoView?.({
      behavior: "smooth",
      block: "center",
    });
  }

  function askAboutInsight(card) {
    setAiQuestion(card.question);
    setAiResult(null);
    setAiError("");
    document.getElementById("analytics-assistant")?.scrollIntoView?.({
      behavior: "smooth",
      block: "center",
    });
  }

  return (
    <div className="feature-page analytics-page">
      <header className="feature-page-header analytics-header">
        <div>
          <h1>Analytics</h1>
          <p>Find spending patterns, compare periods, and see which commitments may need attention.</p>
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

      <section className="analytics-kpi-grid" aria-label="Cash flow and fee totals">
        <article><span>Income</span><strong>{formatCurrency(cashFlow.income || 0)}</strong><small>Recorded inflows</small></article>
        <article><span>Recorded spending</span><strong>{formatCurrency(cashFlow.recordedExpenses || 0)}</strong><small>Before provider fees</small></article>
        <article><span>Confirmed fees</span><strong>{formatCurrency(cashFlow.confirmedTransactionFees || 0)}</strong><small>Provider-reported or user-confirmed</small></article>
        <article><span>Estimated fees</span><strong>{formatCurrency(cashFlow.estimatedTransactionFees || 0)}</strong><small>Versioned estimates—review before relying on them</small></article>
      </section>

      <section className="analytics-insights" aria-labelledby="analytics-insights-title">
        <header className="analytics-insights-header">
          <div>
            <span>Moneytiqx insights</span>
            <h2 id="analytics-insights-title">What deserves attention</h2>
            <p>Specific signals from your records, with the calculation window and a useful next step.</p>
          </div>
          <div className="analytics-insights-meta">
            <span><i aria-hidden="true" /> Calculated from your records</span>
            <button type="button" onClick={loadSummary} disabled={loading}>
              <RefreshCw size={14} className={loading ? "is-spinning" : ""} />
              Refresh
            </button>
          </div>
        </header>

        <div className="analytics-insight-grid">
          {visibleInsightCards.map((card) => (
            <article className={`analytics-insight-card severity-${card.severity}`} key={`${card.type}-${card.title}`}>
              <div className="analytics-insight-card-topline">
                <span>{card.label}</span>
                <div>
                  <strong>{card.metric}</strong>
                  <button type="button" onClick={() => dismissInsight(card)} aria-label={`Hide ${card.title}`} title="Hide this insight">
                    <X size={14} />
                  </button>
                </div>
              </div>
              <h3>{card.title}</h3>
              <p>{card.supporting}</p>
              <div className="analytics-insight-context">
                <span>{insightPeriod}</span>
                <span>{periodTransactionCount} transaction{periodTransactionCount === 1 ? "" : "s"} reviewed</span>
                <span>{card.comparison}</span>
              </div>
              <small>{card.caveat}</small>
              <button type="button" className="analytics-insight-correction" onClick={() => reviewInsight(card)}>
                Something looks wrong? Check the records
              </button>
              <footer>
                <button type="button" onClick={() => reviewInsight(card)}>
                  {card.actionLabel} <MoveRight size={14} />
                </button>
                <button type="button" className="ask" onClick={() => askAboutInsight(card)}>
                  <MessageCircle size={14} /> Explain with AI
                </button>
              </footer>
            </article>
          ))}
          {visibleInsightCards.length === 0 && (
            <div className="analytics-insights-empty">
              <strong>No insights showing</strong>
              <span>You hid every insight for this visit. Undo below or change the period to bring them back.</span>
            </div>
          )}
        </div>
        {lastDismissedInsight && (
          <div className="analytics-insight-feedback" role="status">
            <span>Hidden for this visit. Your financial records were not changed.</span>
            <button type="button" onClick={undoDismissInsight}>Undo</button>
          </div>
        )}
        {lastUpdated && (
          <small className="analytics-insights-updated">
            Updated {lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </small>
        )}
      </section>

      <section className="analytics-visual-grid">
        <article className="analytics-panel analytics-lead-chart" id="analytics-cash-flow">
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

        <section className="analytics-panel analytics-search-panel">
          <header>
            <div><span>Your wording, measured</span><h2>Find a spending habit</h2><p>Search any description or merchant, then compare frequency or value.</p></div>
          </header>
          <form className="analytics-search-form" onSubmit={searchTrend}>
            <label className="analytics-search-input">
              <span className="sr-only">Description or merchant</span>
              <Search size={17} aria-hidden="true" />
              <input value={trendQuery} onChange={(event) => setTrendQuery(event.target.value)} placeholder="Try airtime, sugarcane, supermarket…" maxLength={100} />
            </label>
            <select aria-label="Search period" value={trendPeriod} onChange={(event) => setTrendPeriod(event.target.value)}>
              {SEARCH_PERIODS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}
            </select>
            <button type="submit" className="analytics-refresh-button" disabled={trendLoading}>
              {trendLoading ? <RefreshCw size={15} className="is-spinning" /> : <Search size={15} />}
              Analyse
            </button>
          </form>
          {trendError && <p className="analytics-form-error" role="alert">{trendError}</p>}
          {trend && (
            <>
              <div className="analytics-search-result-head">
                <div><strong>“{trend.query}”</strong><small>{trend.totalCount} matches · {formatCurrency(trend.totalAmount)}</small></div>
                <div className="analytics-metric-toggle" aria-label="Trend metric">
                  <button type="button" className={trendMetric === "amount" ? "active" : ""} onClick={() => setTrendMetric("amount")}>Amount</button>
                  <button type="button" className={trendMetric === "count" ? "active" : ""} onClick={() => setTrendMetric("count")}>Frequency</button>
                </div>
              </div>
              {trend.totalCount > 0
                ? <EChart option={trendOption} ariaLabel={`Spending trend for ${trend.query}`} />
                : <div className="analytics-chart-empty"><span>No owned transactions matched that description or merchant.</span></div>}
            </>
          )}
        </section>

        <section className="analytics-panel analytics-ai-panel" id="analytics-assistant">
          <header>
            <div><span>Grounded assistant</span><h2>Ask about your finances</h2><p>The AI chooses one approved calculation; your database—not the model—produces the figures.</p><small className="analytics-assistant-boundary">Answers only · Nothing changes without your approval</small></div>
            <Sparkles aria-hidden="true" />
          </header>
          <form className="analytics-ai-form" onSubmit={askFinanceAssistant}>
            <textarea value={aiQuestion} onChange={(event) => setAiQuestion(event.target.value)} maxLength={500} placeholder="How many times did I buy airtime this month? Where could I adjust spending?" aria-label="Question about your finances" />
            <div>
              <button type="submit" className="feature-primary-button" disabled={aiLoading || !aiQuestion.trim()}>{aiLoading ? "Checking your data…" : "Ask securely"}</button>
              <button type="button" className="scenario-reset" onClick={loadWeeklySummary} disabled={weeklyLoading}>{weeklyLoading ? "Preparing…" : "Preview weekly review"}</button>
            </div>
          </form>
          {aiError && <p className="analytics-form-error" role="alert">{aiError}</p>}
          {aiResult && (
            <div className="analytics-ai-answer">
              <span className="analytics-ai-label"><Sparkles size={13} /> AI-assisted explanation</span>
              <strong>{aiResult.answer}</strong>
              {(aiResult.evidence || []).map((item) => <p key={item}>{item}</p>)}
              {(aiResult.caveats || []).map((item) => <small key={item}>{item}</small>)}
            </div>
          )}
          {weeklySummary && (
            <div className="analytics-ai-answer weekly">
              <span className="analytics-ai-label"><Sparkles size={13} /> AI-assisted weekly review</span>
              <strong>{weeklySummary.headline}</strong>
              <p>{weeklySummary.summary}</p>
              {(weeklySummary.observations || []).map((item) => <p key={item}>• {item}</p>)}
              {(weeklySummary.options || []).map((item) => <small key={item}>Option: {item}</small>)}
              <small>Preview only. Nothing is sent automatically.</small>
            </div>
          )}
        </section>

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

        <article className="analytics-panel" id="analytics-commitments">
          <header><div><span>Fixed pressure</span><h2>Monthly commitments</h2><p>Bills, subscriptions, debt schedules and goal requirements.</p></div><strong className="analytics-panel-total">{formatCurrency(commitments.totalMonthlyCommitted || 0)}</strong></header>
          <EChart option={commitmentOption} ariaLabel="Horizontal bar chart of estimated monthly commitments" />
        </article>

        <article className="analytics-panel">
          <header><div><span>Plans</span><h2>Budget and goal progress</h2><p>Progress against the current plan, capped visually at the highest observed percentage.</p></div></header>
          <EChart option={progressOption} ariaLabel="Budget use and savings goal progress chart" />
        </article>

        <article className="analytics-panel" id="analytics-debt-position">
          <header><div><span>Liabilities</span><h2>Debt position</h2><p>Current balance compared with activity in the selected period.</p></div></header>
          <EChart option={debtOption} ariaLabel="Debt balance, repayments and recorded fees chart" />
        </article>

        <section className="analytics-panel analytics-scenario-panel" id="analytics-adjustment-lab">
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
        <p>Cash flow comes from your non-deleted transactions. Confirmed provider fees and clearly labelled tariff estimates are added separately; unsupported fees stay unknown rather than becoming invented numbers. Commitments are monthly estimates from active bills, subscriptions, debt schedules and goal gaps. AI may explain an approved calculation, but it never creates these totals or receives database access.</p>
      </section>
    </div>
  );
}

export default Analytics;

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../services/api";
import Analytics from "./Analytics";

vi.mock("../services/api", () => ({
  default: { get: vi.fn() },
}));

vi.mock("../hooks/useAdjustedCurrency", () => ({
  useAdjustedCurrency: () => ({
    formatCurrency: (value) => `KES ${Number(value).toFixed(2)}`,
  }),
}));

vi.mock("../components/analytics/EChart", () => ({
  default: ({ ariaLabel, option }) => {
    const calendarData = option?.series?.[0]?.coordinateSystem === "calendar"
      ? option.series[0].data
      : null;
    const sample = calendarData?.find((item) => item.dayNumber === 18);
    const sampleLabel = sample && option.series[0].label?.formatter
      ? option.series[0].label.formatter({ data: sample })
      : "";
    return (
      <div
        role="img"
        aria-label={ariaLabel}
        data-calendar-days={calendarData?.length}
        data-calendar-sample={sample ? JSON.stringify(sample) : ""}
        data-calendar-label={sampleLabel}
      />
    );
  },
}));

const summary = {
  period: {
    key: "12-months",
    start: "2025-08-19",
    end: "2026-08-18",
    currency: "KES",
  },
  cashFlow: {
    income: "100000.00",
    expenses: "70000.00",
    transactionFees: null,
    net: "30000.00",
    savingsRate: "30.00",
  },
  commitments: {
    monthlyBills: "12000.00",
    monthlySubscriptions: "2500.00",
    monthlyDebtPayments: "8000.00",
    monthlyGoalContributions: "10000.00",
    totalMonthlyCommitted: "32500.00",
    committedIncomePercentage: "32.50",
  },
  budget: {
    planned: "80000.00",
    spent: "60000.00",
    remaining: "20000.00",
    usedPercentage: "75.00",
  },
  debts: {
    activeBalance: "45000.00",
    periodRepayments: "8000.00",
    periodFees: "500.00",
    monthlyScheduledPayments: "8000.00",
  },
  goals: {
    activeCount: 1,
    target: "120000.00",
    saved: "30000.00",
    remaining: "90000.00",
    progressPercentage: "25.00",
    requiredMonthlyContribution: "10000.00",
  },
  monthlyTrend: [
    { month: "2026-08", income: "100000.00", expenses: "70000.00", net: "30000.00" },
  ],
  expenseCategories: [{ category: "Housing", amount: "40000.00" }],
  dailyActivity: [
    { date: "2026-08-18", income: "100000.00", expenses: "70000.00", transactionCount: 3 },
  ],
  adjustmentOpportunities: [
    {
      type: "category_concentration",
      severity: "medium",
      title: "Review Housing spending",
      explanation: "It represents 57.14% of expenses in this period.",
    },
  ],
  warnings: [],
};

beforeEach(() => {
  vi.clearAllMocks();
  api.get.mockResolvedValue({ data: summary });
});

describe("Analytics", () => {
  it("renders reconciled finance sections from the summary API", async () => {
    render(<Analytics />);

    expect(await screen.findByRole("heading", { name: "Analytics" })).toBeInTheDocument();
    expect(screen.getByText("KES 30000.00")).toBeInTheDocument();
    expect(screen.getByText("30.00%")).toBeInTheDocument();
    expect(screen.getByText("KES 32500.00")).toBeInTheDocument();
    expect(screen.getByText("Review Housing spending")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /monthly income, expenses and net/i })).toBeInTheDocument();
    const calendar = screen.getByRole("img", { name: /daily income and expense calendar for 2026-08/i });
    expect(calendar).toHaveAttribute("data-calendar-days", "31");
    expect(calendar).toHaveAttribute("data-calendar-sample", expect.stringContaining('"direction":"income"'));
    expect(calendar.getAttribute("data-calendar-label")).toMatch(/\+.*100K/);
    expect(screen.getByRole("img", { name: /estimated monthly commitments/i })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /budget use and savings goal progress/i })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /debt balance, repayments and recorded fees/i })).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith(
      "/analytics/summary",
      { params: { period: "12-months" } },
    );
  });

  it("requests a new database summary when the period changes", async () => {
    const user = userEvent.setup();
    render(<Analytics />);
    await screen.findByRole("heading", { name: "Analytics" });

    await user.click(screen.getByRole("button", { name: "90 days" }));

    await waitFor(() => expect(api.get).toHaveBeenLastCalledWith(
      "/analytics/summary",
      { params: { period: "90-days" } },
    ));
  });

  it("lets the user explore an unsaved adjustment scenario", async () => {
    const user = userEvent.setup();
    render(<Analytics />);
    await screen.findByRole("heading", { name: "Analytics" });

    expect(screen.getByText(/Nothing here is saved or applied/i)).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Category to explore"), "Housing");
    await user.click(screen.getByRole("button", { name: "Reset assumptions" }));

    expect(screen.getByRole("img", { name: /what-if scenario monthly flexibility/i })).toBeInTheDocument();
  });

  it("explains an empty transaction period without hiding commitments", async () => {
    api.get.mockResolvedValue({
      data: {
        ...summary,
        cashFlow: { income: "0.00", expenses: "0.00", transactionFees: null, net: "0.00", savingsRate: null },
        monthlyTrend: [],
        expenseCategories: [],
        dailyActivity: [],
        adjustmentOpportunities: [],
      },
    });

    render(<Analytics />);

    expect(await screen.findByText("No transaction movement in this period.")).toBeInTheDocument();
    expect(screen.getByText("KES 32500.00")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});

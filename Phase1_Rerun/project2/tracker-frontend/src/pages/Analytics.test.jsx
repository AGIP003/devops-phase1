import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../services/api";
import Analytics from "./Analytics";

const router = vi.hoisted(() => ({ navigate: vi.fn() }));

vi.mock("react-router-dom", () => ({
  useNavigate: () => router.navigate,
}));

vi.mock("../services/api", () => ({
  default: { get: vi.fn(), post: vi.fn() },
}));

vi.mock("../hooks/useAdjustedCurrency", () => ({
  useAdjustedCurrency: () => ({
    currencyCode: "KES",
    rates: { KES: 1 },
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
    recordedExpenses: "69500.00",
    expenses: "70000.00",
    transactionFees: "500.00",
    confirmedTransactionFees: "400.00",
    estimatedTransactionFees: "100.00",
    financingCharges: "20.00",
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
  expenseCategories: [{ category: "Housing", amount: "40000.00", transactionCount: 8 }],
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
  api.post.mockResolvedValue({ data: {} });
});

describe("Analytics", () => {
  it("renders reconciled finance sections from the summary API", async () => {
    render(<Analytics />);

    expect(await screen.findByRole("heading", { name: "Analytics" })).toBeInTheDocument();
    expect(screen.getAllByText("KES 30000.00")).toHaveLength(2);
    expect(screen.getByText("30.00%")).toBeInTheDocument();
    expect(screen.getByText("KES 32500.00")).toBeInTheDocument();
    expect(screen.getByText("Housing is your largest spending area")).toBeInTheDocument();
    expect(screen.getByText("58%")).toBeInTheDocument();
    expect(screen.getByText("KES 40000.00 across 8 transactions")).toBeInTheDocument();
    expect(screen.getAllByText("3 transactions reviewed").length).toBeGreaterThan(0);
    expect(screen.getByText(/Calculated from your records/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open financial assistant" })).toBeInTheDocument();
    expect(screen.queryByRole("dialog", { name: "Ask about your finances" })).not.toBeInTheDocument();
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

  it("searches any description or merchant and lets the user switch metric", async () => {
    const user = userEvent.setup();
    api.get.mockImplementation((url) => {
      if (url === "/analytics/description-trend") {
        return Promise.resolve({
          data: {
            query: "airtime",
            totalCount: 2,
            totalAmount: "350.00",
            series: [{ bucket: "2026-08-18", count: 2, amount: "350.00" }],
            topMerchants: [{ merchant: "Safaricom", count: 2, amount: "350.00" }],
            topDescriptions: [{ description: "Airtime top up", count: 2, amount: "350.00" }],
            recordedHistory: {
              firstTransactionDate: "2026-05-01",
              lastTransactionDate: "2026-08-18",
            },
          },
        });
      }
      return Promise.resolve({ data: summary });
    });
    render(<Analytics />);
    await screen.findByRole("heading", { name: "Analytics" });

    await user.type(screen.getByPlaceholderText(/Try airtime/i), "airtime");
    await user.click(screen.getByRole("button", { name: "Analyse" }));

    expect(await screen.findByText("“airtime”")).toBeInTheDocument();
    expect(screen.getByText("2 matches · KES 350.00")).toBeInTheDocument();
    expect(screen.getByText("Safaricom")).toBeInTheDocument();
    expect(screen.getByText("Airtime top up")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /spending trend for airtime/i })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Frequency" }));
    expect(api.get).toHaveBeenCalledWith(
      "/analytics/description-trend",
      { params: { query: "airtime", period: "month", offset: 0 } },
    );
  });

  it("asks the bounded assistant and previews an opt-in weekly review", async () => {
    const user = userEvent.setup();
    api.post
      .mockResolvedValueOnce({
        data: {
          answer: "You recorded airtime twice this month.",
          evidence: ["2 matches totalling KES 350.00"],
          caveats: ["Only recorded transactions are included."],
        },
      })
      .mockResolvedValueOnce({
        data: {
          generationMode: "data_summary",
          narrative: {
            headline: "A quieter spending week",
            summary: "Recorded outflow decreased.",
            observations: ["Food spending fell."],
            options: ["Review recurring fees."],
            caveats: [],
          },
        },
      });
    render(<Analytics />);
    await screen.findByRole("heading", { name: "Analytics" });

    await user.click(screen.getByRole("button", { name: "Open financial assistant" }));
    expect(screen.getByRole("dialog", { name: "Ask about your finances" })).toBeInTheDocument();

    await user.type(
      screen.getByRole("textbox", { name: "Question about your finances" }),
      "How often did I buy airtime this month?",
    );
    await user.click(screen.getByRole("button", { name: "Ask securely" }));
    expect(await screen.findByText("You recorded airtime twice this month.")).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith(
      "/ai/analytics/questions",
      { question: "How often did I buy airtime this month?" },
    );

    await user.click(screen.getByRole("button", { name: "Preview weekly review" }));
    expect(await screen.findByText("A quieter spending week")).toBeInTheDocument();
    expect(screen.getByText("Weekly review")).toBeInTheDocument();
    expect(screen.getByText("Prepared directly from your recorded data.")).toBeInTheDocument();
    expect(screen.getByText("Preview only. Nothing is sent automatically.")).toBeInTheDocument();
  });

  it("turns an insight into an editable assistant question without submitting it", async () => {
    const user = userEvent.setup();
    render(<Analytics />);
    await screen.findByRole("heading", { name: "What deserves attention" });

    await user.click(screen.getAllByRole("button", { name: "Explain with AI" })[0]);

    expect(screen.getByRole("dialog", { name: "Ask about your finances" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Question about your finances" })).toHaveValue(
      "How much did I spend on Housing in this period, and where could I adjust?",
    );
    expect(api.post).not.toHaveBeenCalled();
  });

  it("closes the assistant drawer with Escape and restores focus to its edge shortcut", async () => {
    const user = userEvent.setup();
    render(<Analytics />);
    await screen.findByRole("heading", { name: "Analytics" });

    const trigger = screen.getByRole("button", { name: "Open financial assistant" });
    await user.click(trigger);
    expect(screen.getByRole("dialog", { name: "Ask about your finances" })).toBeInTheDocument();

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("dialog", { name: "Ask about your finances" })).not.toBeInTheDocument();
    await waitFor(() => expect(trigger).toHaveFocus());
  });

  it("drills into matching records and lets the user hide and restore an insight", async () => {
    const user = userEvent.setup();
    render(<Analytics />);
    await screen.findByRole("heading", { name: "What deserves attention" });

    await user.click(screen.getAllByRole("button", { name: "See transactions" })[0]);
    expect(router.navigate).toHaveBeenCalledWith(
      "/transactions?category=Housing&from=2025-08-19&to=2026-08-18",
    );

    await user.click(screen.getByRole("button", { name: "Hide Housing is your largest spending area" }));
    expect(screen.queryByText("Housing is your largest spending area")).not.toBeInTheDocument();
    expect(screen.getByText(/Your financial records were not changed/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Undo" }));
    expect(screen.getByText("Housing is your largest spending area")).toBeInTheDocument();
  });

  it("explains an empty transaction period without hiding commitments", async () => {
    api.get.mockResolvedValue({
      data: {
        ...summary,
        cashFlow: {
          income: "0.00",
          recordedExpenses: "0.00",
          expenses: "0.00",
          transactionFees: "0.00",
          confirmedTransactionFees: "0.00",
          estimatedTransactionFees: "0.00",
          net: "0.00",
          savingsRate: null,
        },
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

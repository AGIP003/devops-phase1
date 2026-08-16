import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../services/api";
import Debts from "./Debts";


vi.mock("../services/api", () => ({
  default: {
    delete: vi.fn(),
    get: vi.fn(),
    post: vi.fn(),
  },
}));

vi.mock("../hooks/useAdjustedCurrency", () => ({
  useAdjustedCurrency: () => ({
    formatCurrency: (value) => `KES ${Number(value).toFixed(2)}`,
  }),
}));

const debt = {
  id: 7,
  title: "KCB M-PESA loan",
  direction: "i_owe",
  category: "mobile_loan",
  counterparty: "KCB M-PESA",
  currencyCode: "KES",
  trackingKind: "new",
  originalAmount: "10000.00",
  openingBalance: "8000.00",
  currentBalance: "8000.00",
  paidAmount: "2000.00",
  progress: 20,
  openedOn: "2026-08-01",
  notes: "Use the lender-reported balance",
  hasInterest: true,
  statedInterestRate: "8.8000",
  interestPeriod: "fixed",
  status: "active",
  createdVia: "manual",
  schedule: {
    frequency: "one_time",
    intervalCount: 1,
    installmentAmount: "8000.00",
    nextDueDate: "2026-08-30",
    finalDueDate: "2026-08-30",
  },
  feeTerms: [
    { id: 3, feeCategory: "processing", customFeeName: null },
  ],
  entries: [],
};

beforeEach(() => {
  vi.clearAllMocks();
  api.get.mockResolvedValue({ data: [debt] });
  api.delete.mockResolvedValue({ data: { status: "success" } });
  api.post.mockResolvedValue({ data: { data: debt, status: "success" } });
});

describe("Debts", () => {
  it("keeps cards compact, expands details, and closes on an outside click", async () => {
    const user = userEvent.setup();
    render(<Debts />);

    const debtTitle = await screen.findByText("KCB M-PESA loan");
    expect(screen.queryByText("Declared fees")).not.toBeInTheDocument();

    await user.click(debtTitle.closest("button"));
    expect(screen.getByText("Declared fees")).toBeInTheDocument();
    expect(screen.getByText("Use the lender-reported balance")).toBeInTheDocument();

    await user.click(screen.getByRole("heading", { name: "Debts & Loans" }));
    expect(screen.queryByText("Declared fees")).not.toBeInTheDocument();
  });

  it("opens the full Add Debt card and collapses it after saving", async () => {
    const user = userEvent.setup();
    api.get.mockResolvedValue({ data: [] });
    render(<Debts />);

    await screen.findByText("No debts in this view");
    await user.click(screen.getByRole("button", { name: "Add debt" }));

    await user.type(
      screen.getByRole("textbox", { name: "Description" }),
      "Amina lunch advance",
    );
    await user.type(screen.getByLabelText("Original amount"), "8500");
    await user.click(screen.getByRole("checkbox", { name: /fees/i }));
    await user.click(screen.getByRole("checkbox", { name: "Processing fee" }));

    api.post.mockResolvedValue({
      data: {
        data: {
          ...debt,
          id: 8,
          title: "Amina lunch advance",
          category: "other",
          counterparty: null,
          originalAmount: "8500.00",
          openingBalance: "8500.00",
          currentBalance: "8500.00",
          paidAmount: "0.00",
          progress: 0,
          hasInterest: false,
          statedInterestRate: null,
          interestPeriod: null,
          schedule: null,
        },
      },
    });

    await user.click(screen.getByRole("button", { name: "Save debt" }));

    expect(await screen.findByText(/Debt saved/)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Add a debt" })).not.toBeInTheDocument();
    expect(screen.getByText("Amina lunch advance")).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith(
      "/debts",
      expect.objectContaining({
        title: "Amina lunch advance",
        originalAmount: "8500",
        feeTerms: [{ feeCategory: "processing", customFeeName: null }],
      }),
    );
  });

  it("can link a repayment to a normal transaction when the user chooses", async () => {
    const user = userEvent.setup();
    render(<Debts />);
    await user.click((await screen.findByText("KCB M-PESA loan")).closest("button"));
    await user.click(screen.getByRole("button", { name: /record activity/i }));

    const activityForm = screen.getByRole("button", { name: "Save activity" }).closest("form");
    await user.type(within(activityForm).getByLabelText("Amount"), "1000");
    await user.click(within(activityForm).getByRole("checkbox", { name: /also add to transactions/i }));

    api.post.mockResolvedValue({
      data: {
        data: {
          ...debt,
          currentBalance: "7000.00",
          paidAmount: "3000.00",
          progress: 30,
          entries: [
            {
              id: 11,
              entryType: "repayment",
              amount: "1000.00",
              occurredOn: "2026-08-16",
              transactionId: 44,
              createdVia: "manual",
            },
          ],
        },
      },
    });

    await user.click(within(activityForm).getByRole("button", { name: "Save activity" }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      "/debts/7/entries",
      expect.objectContaining({
        amount: "1000",
        createTransaction: true,
        paymentMethod: "m-pesa",
      }),
    ));
    expect(await screen.findByText(/Linked transaction/)).toBeInTheDocument();
  });
});

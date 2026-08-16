import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import SummaryCards from "./SummaryCard";


describe("SummaryCards", () => {
  it("uses live goal and debt records instead of dashboard mocks", async () => {
    const user = userEvent.setup();
    render(
      <SummaryCards
        filteredTransactions={[]}
        debts={[
          {
            id: 8,
            title: "KCB M-PESA loan",
            direction: "i_owe",
            currentBalance: "7000.00",
          },
        ]}
        goals={[
          {
            id: 12,
            name: "Emergency fund",
            targetAmount: "120000.00",
            currentSavings: "25000.00",
            progress: 21,
          },
        ]}
        hideAmounts={false}
        toggleHideAmounts={vi.fn()}
        currencyFormatter={{ format: (value) => `KES ${Number(value).toFixed(2)}` }}
      />,
    );

    expect(screen.getByText("Emergency fund")).toBeInTheDocument();
    expect(screen.getByText("Collected: KES 25000.00")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Debt" }));
    expect(screen.getByText("KES 7000.00")).toBeInTheDocument();
    expect(screen.getByText("0% offset by receivables")).toBeInTheDocument();
  });
});

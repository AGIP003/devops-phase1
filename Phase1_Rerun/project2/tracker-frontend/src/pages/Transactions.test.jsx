import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../services/api";
import Transactions from "./Transactions";


vi.mock("react-router-dom", async (importOriginal) => {
  const original = await importOriginal();
  return {
    ...original,
    useOutletContext: () => ({ toggleSidebar: vi.fn() }),
  };
});

vi.mock("../services/api", () => ({
  default: {
    delete: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
  },
}));

vi.mock("../hooks/useAdjustedCurrency", () => ({
  useAdjustedCurrency: () => ({
    formatCurrency: (value) => `KES ${Number(value).toFixed(2)}`,
  }),
}));

const transactions = [
  {
    id: 1,
    description: "August rent",
    merchant_name: "Landlord",
    type: "expense",
    category: "Housing",
    date: "2026-08-10",
    payment_method: "m-pesa",
    amount: "25000.00",
  },
  {
    id: 2,
    description: "Weekly groceries",
    merchant_name: "Local market",
    type: "expense",
    category: "Food",
    date: "2026-08-11",
    payment_method: "cash",
    amount: "5000.00",
  },
];

beforeEach(() => {
  vi.clearAllMocks();
  api.get.mockResolvedValue({ data: transactions });
});

describe("Transactions analytics drill-down", () => {
  it("opens with the category and date window supplied by an insight", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={[
        "/transactions?category=Housing&from=2026-08-01&to=2026-08-31",
      ]}>
        <Transactions />
      </MemoryRouter>,
    );

    expect(await screen.findByText("August rent")).toBeInTheDocument();
    expect(screen.queryByText("Weekly groceries")).not.toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Filter transactions by category" })).toHaveValue("Housing");
    expect(screen.getByRole("combobox", { name: "Filter transactions by date range" })).toHaveValue("custom");
    expect(screen.getByLabelText("Filter transactions from date")).toHaveValue("2026-08-01");
    expect(screen.getByLabelText("Filter transactions to date")).toHaveValue("2026-08-31");

    await user.click(screen.getByRole("button", { name: "Reset" }));
    expect(screen.getByText("Weekly groceries")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Filter transactions by category" })).toHaveValue("all");
  });
});


import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../services/api";
import Budgets from "./Budgets";

vi.mock("../services/api", () => ({
  default: {
    delete: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

vi.mock("../hooks/useAdjustedCurrency", () => ({
  useAdjustedCurrency: () => ({
    formatCurrency: (value) => `KES ${Number(value).toFixed(2)}`,
  }),
}));

const budget = {
  id: 7,
  name: "Monthly groceries",
  category: "Food",
  targetAmount: "5000.00",
  lastSpend: "0.00",
  items: [
    { id: 11, name: "Rice", estimatedAmount: "1200.00", checked: false },
    { id: 12, name: "Vegetables", estimatedAmount: "800.00", checked: true },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  api.get.mockResolvedValue({ data: [budget] });
});

describe("Budgets", () => {
  it("opens a populated edit form and shows the remaining draft allocation", async () => {
    const user = userEvent.setup();
    render(<Budgets />);

    await user.click(await screen.findByRole("button", { name: "Edit Monthly groceries" }));

    expect(screen.getByRole("form", { name: "Edit budget" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Update the plan" })).toBeInTheDocument();
    expect(screen.getByDisplayValue("Monthly groceries")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Item 1 name" })).toHaveValue("Rice");
    expect(screen.getByText(/KES 2000\.00/)).toBeInTheDocument();
    expect(screen.getByText("KES 3000.00")).toBeInTheDocument();
  });
});

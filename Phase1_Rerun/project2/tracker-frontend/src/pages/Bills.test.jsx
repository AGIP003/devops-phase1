import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../services/api";
import Bills from "./Bills";


vi.mock("../services/api", () => ({
  default: {
    delete: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
    post: vi.fn(),
  },
}));

vi.mock("../hooks/useAdjustedCurrency", () => ({
  useAdjustedCurrency: () => ({
    formatCurrency: (value) => `KES ${Number(value).toFixed(2)}`,
  }),
}));

const electricity = {
  id: 41,
  kind: "bill",
  name: "Electricity",
  provider: "Kenya Power",
  category: "Utilities",
  amount: "2500.00",
  amountKind: "estimated",
  currencyCode: "KES",
  nextDueDate: "2026-08-31",
  frequency: "monthly",
  customIntervalDays: null,
  autoRenews: null,
  status: "active",
  cancelledAt: null,
  overdue: false,
  notes: "Amount changes with usage",
  createdVia: "manual",
  occurrences: [],
};

beforeEach(() => {
  vi.clearAllMocks();
  api.get.mockResolvedValue({ data: [electricity] });
  api.delete.mockResolvedValue({ data: { status: "success" } });
  api.patch.mockResolvedValue({
    data: { data: { ...electricity, status: "cancelled" } },
  });
  api.post.mockResolvedValue({
    data: { data: electricity, status: "success" },
  });
  vi.spyOn(window, "confirm").mockReturnValue(true);
});

describe("Bills and subscriptions", () => {
  it("keeps cards compact and reveals operational details on demand", async () => {
    const user = userEvent.setup();
    render(<Bills />);

    const cardButton = await screen.findByRole("button", {
      name: /bill Electricity 31 Aug 2026/i,
    });
    expect(screen.queryByText("Amount changes with usage")).not.toBeInTheDocument();

    await user.click(cardButton);
    expect(screen.getByText("Amount changes with usage")).toBeInTheDocument();
    expect(screen.getByText("Kenya Power")).toBeInTheDocument();

    await user.click(screen.getByRole("heading", { name: "Bills & Subscriptions" }));
    expect(screen.queryByText("Amount changes with usage")).not.toBeInTheDocument();
  });

  it("creates a subscription without asking whether it is one-time", async () => {
    const user = userEvent.setup();
    api.get.mockResolvedValue({ data: [] });
    const spotify = {
      ...electricity,
      id: 42,
      kind: "subscription",
      name: "Spotify",
      provider: "Spotify",
      category: "Music",
      amount: "490.00",
      amountKind: "fixed",
      autoRenews: true,
    };
    api.post.mockResolvedValue({ data: { data: spotify } });
    render(<Bills />);

    await screen.findByText("No recurring items in this view");
    await user.click(screen.getByRole("button", { name: "Add item" }));
    await user.click(screen.getByRole("radio", { name: "Subscription" }));
    await user.type(screen.getByLabelText("Service name"), "Spotify");
    await user.type(screen.getByLabelText(/Provider/), "Spotify");
    await user.type(screen.getByLabelText(/Category/), "Music");
    await user.type(
      screen.getByRole("spinbutton", { name: "Expected amount" }),
      "490",
    );
    await user.type(screen.getByLabelText("Next due date"), "2026-09-02");

    expect(screen.queryByText(/one-time/i)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Save subscription" }));

    expect(await screen.findByText("Subscription saved.")).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith("/commitments", expect.objectContaining({
      kind: "subscription",
      name: "Spotify",
      amount: "490",
      amountKind: "fixed",
      autoRenews: true,
      frequency: "monthly",
    }));
  });

  it("records an actual payment and receives the advanced due date", async () => {
    const user = userEvent.setup();
    const updated = {
      ...electricity,
      nextDueDate: "2026-09-30",
      occurrences: [{
        id: 81,
        resolution: "paid",
        dueDate: "2026-08-31",
        expectedAmount: "2500.00",
        actualAmount: "2300.00",
        resolvedOn: "2026-08-29",
        notes: "Paid early",
        createdVia: "manual",
      }],
    };
    api.post.mockResolvedValue({ data: { data: updated } });
    render(<Bills />);

    await user.click(await screen.findByRole("button", {
      name: /bill Electricity 31 Aug 2026/i,
    }));
    await user.click(screen.getByRole("button", { name: "Mark paid" }));
    const form = screen.getByRole("button", { name: "Record payment" }).closest("form");
    const amountInput = within(form).getByLabelText("Actual amount paid");
    await user.clear(amountInput);
    await user.type(amountInput, "2300");
    await user.clear(within(form).getByLabelText("Payment date"));
    await user.type(within(form).getByLabelText("Payment date"), "2026-08-29");
    await user.type(within(form).getByLabelText(/Note/), "Paid early");
    await user.click(within(form).getByRole("button", { name: "Record payment" }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      "/commitments/41/cycles",
      expect.objectContaining({
        resolution: "paid",
        actualAmount: "2300",
        resolvedOn: "2026-08-29",
      }),
    ));
    expect(await screen.findByText(/Payment recorded and the next due date advanced/)).toBeInTheDocument();
  });

  it("stops recurrence without deleting the card", async () => {
    const user = userEvent.setup();
    render(<Bills />);

    await user.click(await screen.findByRole("button", {
      name: /bill Electricity 31 Aug 2026/i,
    }));
    await user.click(screen.getByRole("button", { name: "Stop recurrence" }));

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith(
      "/commitments/41/status",
      { status: "cancelled" },
    ));
    expect(screen.getAllByText("Electricity").length).toBeGreaterThan(0);
    expect(await screen.findByText("Recurrence stopped.")).toBeInTheDocument();
  });

  it("uses a stored provider mark and edits a recorded payment", async () => {
    const user = userEvent.setup();
    const occurrence = {
      id: 81,
      resolution: "paid",
      dueDate: "2026-08-31",
      expectedAmount: "490.00",
      actualAmount: "490.00",
      resolvedOn: "2026-08-29",
      notes: "Spotify payment",
      createdVia: "manual",
    };
    const spotify = {
      ...electricity,
      kind: "subscription",
      name: "Spotify Premium",
      provider: "Spotify",
      amount: "490.00",
      amountKind: "fixed",
      autoRenews: true,
      occurrences: [occurrence],
    };
    api.get.mockResolvedValue({ data: [spotify] });
    api.patch.mockResolvedValue({
      data: { data: { ...spotify, occurrences: [{ ...occurrence, actualAmount: "450.00" }] } },
    });
    const { container } = render(<Bills />);

    expect((await screen.findAllByText("Spotify Premium")).length).toBeGreaterThan(0);
    expect(container.querySelector(".subscription-icon-spotify")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /subscription Spotify Premium/i }));
    await user.click(screen.getByRole("button", { name: /history \(1\)/i }));
    await user.click(screen.getByRole("button", { name: /edit spotify payment/i }));
    const amount = screen.getByLabelText("Edit actual amount paid");
    await user.clear(amount);
    await user.type(amount, "450");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith(
      "/commitments/41/cycles/81",
      expect.objectContaining({ actualAmount: "450" }),
    ));
  });
});

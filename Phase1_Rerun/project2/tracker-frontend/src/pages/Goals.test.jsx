import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../services/api";
import Goals from "./Goals";


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

const goal = {
  id: 12,
  name: "Emergency fund",
  targetAmount: "120000.00",
  currentSavings: "20000.00",
  remainingAmount: "100000.00",
  targetDate: "2026-12-31",
  contributionFrequency: "monthly",
  suggestedContribution: "20000.00",
  remainingPeriods: 5,
  progress: 16,
  overdue: false,
  targetReached: false,
  currencyCode: "KES",
  notes: "Three months of essential expenses",
  createdVia: "manual",
  entries: [
    {
      id: 30,
      entryType: "contribution",
      amount: "20000.00",
      occurredOn: "2026-08-16",
      notes: "Opening savings",
      createdVia: "manual",
    },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  api.get.mockResolvedValue({ data: [goal] });
  api.delete.mockResolvedValue({ data: { status: "success" } });
  api.post.mockResolvedValue({ data: { data: goal, status: "success" } });
  api.patch.mockResolvedValue({ data: { data: goal, status: "success" } });
});

describe("Goals", () => {
  it("keeps the mock card compact and reveals details and activity on demand", async () => {
    const user = userEvent.setup();
    render(<Goals />);

    const title = await screen.findByText("Emergency fund");
    expect(screen.queryByText("Still needed")).not.toBeInTheDocument();
    expect(screen.queryByText("Opening savings")).not.toBeInTheDocument();

    await user.click(title.closest("button"));
    expect(screen.getByText("Still needed")).toBeInTheDocument();
    expect(screen.queryByText("Opening savings")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /view activity/i }));
    expect(screen.getByText("Opening savings")).toBeInTheDocument();

    await user.click(screen.getByRole("heading", { name: "Savings & Goals" }));
    expect(screen.queryByText("Still needed")).not.toBeInTheDocument();
  });

  it("creates a goal from the full form and collapses it after saving", async () => {
    const user = userEvent.setup();
    api.get.mockResolvedValue({ data: [] });
    render(<Goals />);

    await screen.findByText("No savings goals yet");
    await user.click(screen.getByRole("button", { name: "Add goal" }));
    await user.type(screen.getByLabelText("Goal name"), "Graduation trip");
    await user.type(
      screen.getByRole("spinbutton", { name: "Target amount" }),
      "90000",
    );
    await user.type(
      screen.getByRole("spinbutton", { name: "Already saved" }),
      "10000",
    );
    await user.type(screen.getByLabelText("Target date"), "2026-12-31");
    await user.selectOptions(screen.getByLabelText("Saving frequency"), "fortnightly");

    api.post.mockResolvedValue({
      data: {
        data: {
          ...goal,
          id: 13,
          name: "Graduation trip",
          targetAmount: "90000.00",
          currentSavings: "10000.00",
          contributionFrequency: "fortnightly",
        },
      },
    });

    await user.click(screen.getByRole("button", { name: "Save goal" }));

    expect(await screen.findByText(/Goal saved/)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Add a savings goal" })).not.toBeInTheDocument();
    expect(screen.getByText("Graduation trip")).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith("/goals", expect.objectContaining({
      name: "Graduation trip",
      targetAmount: "90000",
      currentSavings: "10000",
      contributionFrequency: "fortnightly",
    }));
  });

  it("records savings without creating or linking a transaction", async () => {
    const user = userEvent.setup();
    render(<Goals />);
    await user.click((await screen.findByText("Emergency fund")).closest("button"));
    await user.click(screen.getByRole("button", { name: "Update savings" }));

    const form = screen.getByRole("button", { name: "Save update" }).closest("form");
    await user.type(within(form).getByLabelText("Amount"), "5000");
    await user.type(within(form).getByLabelText(/Note/), "August saving");

    api.post.mockResolvedValue({
      data: {
        data: {
          ...goal,
          currentSavings: "25000.00",
          remainingAmount: "95000.00",
          entries: [
            {
              id: 31,
              entryType: "contribution",
              amount: "5000.00",
              occurredOn: "2026-08-16",
              notes: "August saving",
              createdVia: "manual",
            },
            ...goal.entries,
          ],
        },
      },
    });

    await user.click(within(form).getByRole("button", { name: "Save update" }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      "/goals/12/entries",
      expect.objectContaining({
        entryType: "contribution",
        amount: "5000",
        notes: "August saving",
      }),
    ));
    const payload = api.post.mock.calls.at(-1)[1];
    expect(payload).not.toHaveProperty("transactionId");
    expect(payload).not.toHaveProperty("createTransaction");
  });

  it("edits the activity that produced the saved total", async () => {
    const user = userEvent.setup();
    api.patch.mockResolvedValue({
      data: {
        data: {
          ...goal,
          currentSavings: "5000.00",
          remainingAmount: "115000.00",
          entries: [{ ...goal.entries[0], amount: "5000.00" }],
        },
      },
    });
    render(<Goals />);

    await user.click((await screen.findByText("Emergency fund")).closest("button"));
    await user.click(screen.getByRole("button", { name: /view activity/i }));
    await user.click(screen.getByRole("button", { name: /edit opening savings/i }));

    const amount = screen.getByLabelText("Edit savings amount");
    await user.clear(amount);
    await user.type(amount, "5000");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith(
      "/goals/12/entries/30",
      expect.objectContaining({ amount: "5000" }),
    ));
    expect(await screen.findByText("Savings activity corrected.")).toBeInTheDocument();
  });
});

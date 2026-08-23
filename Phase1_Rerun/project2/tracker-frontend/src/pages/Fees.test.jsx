import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../services/api";
import Fees from "./Fees";


vi.mock("../services/api", () => ({
  default: { get: vi.fn(), post: vi.fn() },
}));

vi.mock("../hooks/useAdjustedCurrency", () => ({
  useAdjustedCurrency: () => ({
    formatCurrency: (value) => `KES ${Number(value).toFixed(2)}`,
  }),
}));

const summary = {
  period: {
    monthStart: "2026-08-01",
    weekStart: "2026-08-17",
    end: "2026-08-23",
    currency: "KES",
  },
  totalWeek: "112.00",
  totalMonth: "186.00",
  confirmedMonth: "180.00",
  estimatedMonth: "6.00",
  unknownFeeCount: 2,
  feeShareOfOutflows: "1.24",
  providerTotals: [
    { provider: "airtel_money", total: "106.00", count: 2 },
    { provider: "fuliza_mpesa", total: "80.00", count: 1 },
  ],
  recentEvents: [
    {
      id: "transaction-4",
      provider: "airtel_money",
      description: "Transfer to Pamela",
      date: "2026-08-20",
      amount: "15000.00",
      fee: "100.00",
      source: "provider_reported",
    },
  ],
  catalogVersion: "kenya-public-tariffs-2026-08-23",
};

const catalog = {
  version: "kenya-public-tariffs-2026-08-23",
  currency: "KES",
  services: [
    {
      provider: "airtel_money",
      service: "other_network",
      name: "Airtel to another network",
      helper: "Use this when the recipient is not on Airtel.",
      source: "https://www.airtelkenya.com/tariffs_charges",
      sourceLabel: "Airtel Money current tariff guide",
      effectiveLabel: "Current page checked 23 Aug 2026",
      bands: [
        { upTo: "100", fee: "0" },
        { upTo: "500", fee: "6" },
      ],
    },
    {
      provider: "airtel_money",
      service: "on_net",
      name: "Airtel to Airtel",
      helper: "Published as free across all bands.",
      source: "https://www.airtelkenya.com/tariffs_charges",
      sourceLabel: "Airtel Money current tariff guide",
      effectiveLabel: "Current page checked 23 Aug 2026",
      bands: [{ upTo: "250000", fee: "0" }],
      estimationAvailable: true,
    },
    {
      provider: "mpesa",
      service: "send_money",
      name: "M-PESA Send Money",
      helper: "Estimate from the published table and confirm the final charge.",
      source: "https://www.safaricom.co.ke/images/Downloads/M-PESA-BULK-PAYMENT-TARIFF-FORM.pdf",
      sourceLabel: "Safaricom M-PESA registered-wallet tariff form",
      effectiveLabel: "Public Safaricom form checked 23 Aug 2026",
      bands: [
        { upTo: "100", fee: "0" },
        { upTo: "500", fee: "7" },
      ],
      estimationAvailable: true,
    },
    {
      provider: "fuliza_mpesa",
      service: "maintenance_fee",
      name: "Fuliza daily maintenance fee",
      helper: "Monitor recurring maintenance charges.",
      source: "https://www.safaricom.co.ke/",
      sourceLabel: "Safaricom Fuliza pricing announcement",
      effectiveLabel: "Terms vary by amount and duration",
      bands: [],
      estimationAvailable: false,
    },
  ],
  bankReferences: [
    {
      name: "KCB Bank Kenya",
      sourceLabel: "Tariff guide effective April 2026",
      source: "https://ke.kcbgroup.com/our-tariffs",
      note: "Charges depend on account, channel and transaction type.",
    },
  ],
  warning: "Tariffs can change.",
};

beforeEach(() => {
  vi.clearAllMocks();
  api.get.mockImplementation((url) => Promise.resolve({
    data: url === "/fees/summary" ? summary : catalog,
  }));
  api.post.mockResolvedValue({
    data: {
      provider: "airtel_money",
      service: "other_network",
      serviceName: "Airtel to another network",
      amount: "500.00",
      estimatedFee: "6.00",
      source: "https://www.airtelkenya.com/tariffs_charges",
      sourceLabel: "Airtel Money current tariff guide",
      warning: "Estimate only. Confirm the final charge.",
    },
  });
});

describe("Fees", () => {
  it("renders owner-scoped fee evidence and sourced references", async () => {
    render(<Fees />);

    expect(await screen.findByRole("heading", { name: "Transaction Fees" })).toBeInTheDocument();
    expect(screen.getByText("KES 186.00")).toBeInTheDocument();
    expect(screen.getByText("KES 180.00")).toBeInTheDocument();
    expect(screen.getByText("Transfer to Pamela")).toBeInTheDocument();
    expect(screen.getByText("KCB Bank Kenya")).toBeInTheDocument();
    expect(screen.getByText(/2 imported fees still unknown/i)).toBeInTheDocument();
    expect(screen.queryByText(/mock/i)).not.toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith("/fees/summary");
    expect(api.get).toHaveBeenCalledWith("/fees/tariffs");
  });

  it("calculates a published estimate and expands its tariff bands", async () => {
    const user = userEvent.setup();
    render(<Fees />);
    await screen.findByRole("heading", { name: "Transaction Fees" });

    const amount = screen.getByRole("spinbutton", { name: "Amount (KES)" });
    await user.clear(amount);
    await user.type(amount, "500");
    await user.click(screen.getByRole("button", { name: "Estimate fee" }));

    expect(await screen.findByText("Published-band estimate")).toBeInTheDocument();
    expect(screen.getAllByText("KES 6.00").length).toBeGreaterThan(0);
    expect(api.post).toHaveBeenCalledWith("/fees/estimate", {
      provider: "airtel_money",
      service: "other_network",
      amount: "500",
    });

    await user.click(screen.getByRole("button", {
      name: "View tariff bands for Airtel to another network",
    }));
    await waitFor(() => expect(screen.getByText("Up to KES 100")).toBeInTheDocument());
  });

  it("estimates M-PESA from its table while keeping Fuliza evidence-only", async () => {
    const user = userEvent.setup();
    render(<Fees />);
    await screen.findByRole("heading", { name: "Transaction Fees" });

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Fee type" }),
      "mpesa:send_money",
    );

    expect(screen.getByRole("button", { name: "Estimate fee" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Estimate fee" }));
    expect(api.post).toHaveBeenLastCalledWith("/fees/estimate", {
      provider: "mpesa",
      service: "send_money",
      amount: "1000",
    });

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Fee type" }),
      "fuliza_mpesa:maintenance_fee",
    );

    expect(screen.getByText("Use the confirmed charge")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Estimate fee" })).not.toBeInTheDocument();
    expect(screen.getAllByText("Tracked from your records").length).toBeGreaterThan(0);
  });
});

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../services/api";
import Dashboard from "./Dashboard";


const router = vi.hoisted(() => ({ navigate: vi.fn(), toggleSidebar: vi.fn() }));

vi.mock("react-router-dom", () => ({
  useNavigate: () => router.navigate,
  useOutletContext: () => ({ toggleSidebar: router.toggleSidebar }),
}));

vi.mock("../services/api", () => ({
  default: { get: vi.fn() },
}));

vi.mock("../utils/auth", () => ({
  getCurrentUser: () => ({ username: "jay", display_name: "Jay" }),
}));

vi.mock("../hooks/useAdjustedCurrency", () => ({
  useAdjustedCurrency: () => ({
    formatCurrency: (value) => `KES ${Number(value).toFixed(2)}`,
  }),
}));

vi.mock("../components/auth/AddTransactionForm", () => ({
  default: () => <div>Add transaction form</div>,
}));

vi.mock("../components/ui/ChartsSection", () => ({
  default: () => <div>Category chart</div>,
  MonthlyTrendChart: () => <div>Monthly chart</div>,
}));

vi.mock("../components/ui/SummaryCard", () => ({
  default: () => <div>Summary cards</div>,
}));

vi.mock("../components/ui/TelegramLinkPanel", () => ({
  TelegramIcon: () => <span>Telegram</span>,
}));

vi.mock("../components/ui/SubscriptionIcon", () => ({
  default: () => <span>Subscription</span>,
}));

vi.mock("../components/ui/ProfileMenu", () => ({
  default: () => <div>Profile</div>,
}));

const feeSummary = {
  totalMonth: "186.00",
  totalWeek: "112.00",
  estimatedMonth: "6.00",
  providerTotals: [
    { provider: "airtel_money", total: "106.00", count: 2 },
    { provider: "fuliza_mpesa", total: "80.00", count: 1 },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  api.get.mockImplementation((url) => {
    if (url === "/fees/summary") {
      return Promise.resolve({ data: feeSummary });
    }
    return Promise.resolve({ data: [] });
  });
});

describe("Dashboard fee preview", () => {
  it("uses the live fee summary and links to the full tracker", async () => {
    const user = userEvent.setup();
    render(<Dashboard />);

    await screen.findByRole("heading", { name: "Welcome, Jay" });
    await user.click(screen.getByRole("button", { name: "Fees" }));

    expect(await screen.findByText("KES 186.00")).toBeInTheDocument();
    expect(screen.getByText(/highest: Airtel Money/i)).toBeInTheDocument();
    expect(screen.getByText("KES 112.00 this week")).toBeInTheDocument();
    expect(screen.getByText("KES 6.00 estimated")).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith("/fees/summary");

    await user.click(screen.getByRole("button", { name: "View fee tracker" }));
    expect(router.navigate).toHaveBeenCalledWith("/fees");
  });
});


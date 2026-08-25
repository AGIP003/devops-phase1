import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../services/api";
import Stocks from "./Stocks";


vi.mock("../services/api", () => ({
  default: { get: vi.fn() },
}));

vi.mock("../components/analytics/EChart", () => ({
  default: ({ ariaLabel }) => <div role="img" aria-label={ariaLabel} />,
}));

const stocks = [
  {
    symbol: "SCOM.KE", ticker: "SCOM", name: "Safaricom PLC",
    price: "37.25", changePercent: "1.776", currency: "KES",
    sector: "Telecommunications", lastPriceUpdate: "2026-08-25T16:45:15+00:00",
  },
  {
    symbol: "KCB.KE", ticker: "KCB", name: "KCB Group PLC",
    price: "93.00", changePercent: "-1.25", currency: "KES",
    sector: "Financials", lastPriceUpdate: "2026-08-25T16:45:15+00:00",
  },
  {
    symbol: "KEGN.KE", ticker: "KEGN", name: "KenGen PLC",
    price: "8.40", changePercent: "0.50", currency: "KES",
    sector: "Utilities", lastPriceUpdate: "2026-08-25T16:45:15+00:00",
  },
];

const marketResponse = {
  data: {
    stocks,
    source: {
      name: "mystocks.africa",
      url: "https://mystocks.africa/exchanges/nse-kenya",
      license: "CC BY 4.0",
    },
    sourceUpdatedAt: "2026-08-25T16:45:15+00:00",
    fetchedAt: "2026-08-26T08:00:00+00:00",
    stale: false,
  },
};

const detailResponse = {
  data: {
    stock: {
      ...stocks[0],
      description: "A listed telecommunications company.",
      industry: "Telecommunication services",
      isin: "KE1000001402",
      marketCap: "1490000000000",
      peRatio: null,
      eps: null,
      dividendYield: null,
      dividendPerShare: null,
      volume: "1200000",
      priceHistory: [
        { date: "2026-08-24", price: "36.60" },
        { date: "2026-08-25", price: "37.25" },
      ],
      performance: { "1M": "5.4", YTD: "20.6", "1Y": null },
    },
  },
};

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
  api.get.mockImplementation((url) => {
    if (url === "/nse/stocks") return Promise.resolve(marketResponse);
    if (url.includes("SCOM.KE")) return Promise.resolve(detailResponse);
    return Promise.resolve({ data: { stock: { ...detailResponse.data.stock } } });
  });
});

describe("Stocks market watch", () => {
  it("loads licensed market data and filters without replacing the watchlist", async () => {
    const user = userEvent.setup();
    render(<Stocks />);

    expect(await screen.findByText("Licensed delayed market data")).toBeInTheDocument();
    const explorer = screen.getByRole("heading", { name: "Find a listed company" }).closest("main");
    await user.type(within(explorer).getByPlaceholderText("Search company, ticker or sector"), "KenGen");

    expect(within(explorer).getByText("KenGen PLC")).toBeInTheDocument();
    expect(within(explorer).queryByText("Safaricom PLC")).not.toBeInTheDocument();
    expect(screen.getByText("1 company")).toBeInTheDocument();
  });

  it("persists a device watchlist using the production storage key", async () => {
    const user = userEvent.setup();
    render(<Stocks />);
    await screen.findByText("KCB Group PLC");

    const kcbRow = screen.getByText("KCB Group PLC").closest("article");
    await user.click(within(kcbRow).getByRole("button", { name: "Save KCB to watchlist" }));

    expect(JSON.parse(localStorage.getItem("nse-watchlist-v1"))).toContain("KCB");
  });

  it("opens company evidence and labels unavailable ratios honestly", async () => {
    const user = userEvent.setup();
    render(<Stocks />);
    const explorer = (await screen.findByRole("heading", { name: "Find a listed company" })).closest("main");
    const safaricomRow = within(explorer).getByText("Safaricom PLC").closest("article");
    await user.click(within(safaricomRow).getByRole("button", { name: "View" }));

    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByRole("heading", { name: "Safaricom PLC" })).toBeInTheDocument();
    expect(within(dialog).getByRole("img", { name: /supplied price history/i })).toBeInTheDocument();
    expect(within(dialog).getAllByText("Not supplied").length).toBeGreaterThan(0);
    expect(within(dialog).getByText(/P\/B, ROE.*not supplied by this source/i)).toBeInTheDocument();
  });

  it("loads detail evidence when companies are added to comparison", async () => {
    const user = userEvent.setup();
    render(<Stocks />);
    await screen.findByRole("heading", { name: "Find a listed company" });

    await user.click(screen.getByRole("button", { name: "Add SCOM to comparison" }));

    expect(await screen.findByRole("heading", { name: "Company comparison" })).toBeInTheDocument();
    await waitFor(() => expect(api.get).toHaveBeenCalledWith("/nse/stocks/SCOM.KE"));
    expect(screen.getByText(/MoneyTiq does not manufacture financial ratios/i)).toBeInTheDocument();
  });

  it("identifies stale fallback data instead of presenting it as current", async () => {
    api.get.mockResolvedValueOnce({ data: { ...marketResponse.data, stale: true } });
    render(<Stocks />);
    expect(await screen.findByText("Showing last validated market data")).toBeInTheDocument();
  });
});

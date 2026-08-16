import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdjustedCurrencyProvider } from "../context/AdjustedCurrencyContext";
import api from "../services/api";
import Forex from "./Forex";


vi.mock("../services/api", () => ({
  default: {
    get: vi.fn(),
  },
}));

const liveResponse = {
  data: {
    base: "KES",
    provider: "CBK",
    rateDate: "2026-08-14",
    fetchedAt: "2026-08-16T10:00:00+00:00",
    stale: false,
    rates: {
      KES: "1",
      AED: "0.02843",
      AUD: "0.01095",
      BIF: "23.13",
      CAD: "0.01077",
      CHF: "0.00629",
      CNY: "0.05219",
      DKK: "0.05013",
      USD: "0.00774",
      EUR: "0.0067",
      GBP: "0.00573",
      HKD: "0.06072",
      INR: "0.74074",
      JPY: "1.2327",
      NOK: "0.07348",
      RWF: "11.36",
      SAR: "0.02905",
      SEK: "0.07391",
      SGD: "0.0099",
      UGX: "28.7",
      TZS: "20.46",
      ZAR: "0.12531",
    },
  },
};

function renderForex() {
  render(
    <AdjustedCurrencyProvider>
      <Forex />
    </AdjustedCurrencyProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  api.get.mockResolvedValue(liveResponse);
});

describe("Forex", () => {
  it("renders validated CBK rates and updates the display currency", async () => {
    const user = userEvent.setup();
    renderForex();

    expect(await screen.findByText("Current CBK rates")).toBeInTheDocument();
    expect(screen.getByText(/CBK reference rates, dated 2026-08-14/i)).toBeInTheDocument();

    const usdCard = screen.getByText("US Dollar").closest("button");
    expect(within(usdCard).getByText("0.00774")).toBeInTheDocument();
    expect(screen.getByText("Japanese Yen")).toBeInTheDocument();

    await user.click(usdCard);
    expect(localStorage.getItem("adjustedCurrency")).toBe("USD");
    expect(screen.getAllByText("US$77.40").length).toBeGreaterThan(0);
  });

  it("converts between two non-KES selections through the shared KES rates", async () => {
    const user = userEvent.setup();
    renderForex();

    await screen.findByText("Current CBK rates");
    await user.clear(screen.getByLabelText("Amount"));
    await user.type(screen.getByLabelText("Amount"), "100");
    await user.selectOptions(screen.getByLabelText("From"), "USD");
    await user.selectOptions(screen.getByLabelText("To"), "EUR");

    expect(screen.getByText("€86.5633")).toBeInTheDocument();
    expect(screen.getByText(/1 USD = 0.865633 EUR/)).toBeInTheDocument();
  });

  it("filters the expanded currency list by name or code", async () => {
    const user = userEvent.setup();
    renderForex();

    await screen.findByText("Current CBK rates");
    await user.type(screen.getByRole("searchbox", { name: "Search currencies" }), "JPY");

    expect(screen.getByText("Japanese Yen")).toBeInTheDocument();
    expect(screen.queryByText("US Dollar")).not.toBeInTheDocument();
  });

  it("labels a last-known-good response instead of pretending it is live", async () => {
    api.get.mockResolvedValue({
      data: { ...liveResponse.data, stale: true },
    });

    renderForex();

    expect(await screen.findByText("Last known rates")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("last validated rates");
  });

  it("allows the user to check for updates without reloading the page", async () => {
    const user = userEvent.setup();
    renderForex();

    const refreshButton = await screen.findByRole("button", {
      name: "Refresh",
    });
    await user.click(refreshButton);

    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(2));
  });
});

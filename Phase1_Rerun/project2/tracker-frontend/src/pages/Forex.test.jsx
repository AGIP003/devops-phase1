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
      USD: "0.00774",
      EUR: "0.0067",
      GBP: "0.00573",
      UGX: "28.7",
      TZS: "20.46",
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
    expect(screen.getByText(/via Frankfurter, dated 2026-08-14/i)).toBeInTheDocument();

    const usdCard = screen.getByText("US Dollar").closest("button");
    expect(within(usdCard).getByText("0.00774")).toBeInTheDocument();

    await user.click(usdCard);
    expect(localStorage.getItem("adjustedCurrency")).toBe("USD");
    expect(screen.getByText("US$77.40")).toBeInTheDocument();
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
      name: "Check for updates",
    });
    await user.click(refreshButton);

    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(2));
  });
});

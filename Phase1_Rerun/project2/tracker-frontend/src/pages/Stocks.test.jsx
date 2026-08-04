import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import Stocks from "./Stocks";

describe("Stocks mock", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("filters the company explorer without hiding the saved watchlist", async () => {
    const user = userEvent.setup();
    render(<Stocks />);

    const explorer = screen
      .getByRole("heading", { name: "Choose companies to follow" })
      .closest("section");

    await user.type(
      within(explorer).getByPlaceholderText("Search name, ticker, or sector"),
      "KenGen"
    );

    expect(within(explorer).getByText("KenGen PLC")).toBeInTheDocument();
    expect(within(explorer).queryByText("Safaricom PLC")).not.toBeInTheDocument();
    expect(screen.getByText("Safaricom PLC")).toBeInTheDocument();
  });

  it("adds a company to the watchlist and persists the mock choice", async () => {
    const user = userEvent.setup();
    render(<Stocks />);

    const kcbCard = screen.getByText("KCB Group PLC").closest("article");
    await user.click(within(kcbCard).getByRole("button", { name: "Follow company" }));

    expect(within(kcbCard).getByRole("button", { name: "Following" })).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem("mock-nse-watchlist"))).toContain("KCB");
  });
});

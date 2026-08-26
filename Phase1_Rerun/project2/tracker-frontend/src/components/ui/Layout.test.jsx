import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../../services/api";
import Layout from "./Layout";

vi.mock("../../services/api", () => ({
  default: { get: vi.fn() },
}));

vi.mock("../../utils/auth", () => ({
  removeAuthSession: vi.fn(),
}));

vi.mock("./TelegramLinkPanel", () => ({
  default: () => null,
  TelegramIcon: () => <span aria-hidden="true">Telegram</span>,
}));

beforeEach(() => {
  vi.clearAllMocks();
  api.get.mockResolvedValue({ data: { linked: false } });
});

describe("Layout navigation", () => {
  it("collapses and expands the shared navigation for every nested page", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<h1>Nested page</h1>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    const shell = container.querySelector(".app-shell");
    expect(shell).not.toHaveClass("sidebar-collapsed");

    await user.click(screen.getByRole("button", { name: "Collapse navigation" }));
    expect(shell).toHaveClass("sidebar-collapsed");

    await user.click(screen.getByRole("button", { name: "Expand navigation" }));
    expect(shell).not.toHaveClass("sidebar-collapsed");
  });
});

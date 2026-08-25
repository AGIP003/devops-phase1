import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../services/api";
import Quotations from "./Quotations";

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

const project = {
  id: 41,
  title: "Office chairs",
  category: "Equipment",
  notes: "Delivered to Nairobi",
  currencyCode: "KES",
  status: "comparing",
  preferredQuoteId: null,
  items: [
    { id: 1, name: "Chair", quantity: "2.00", unit: "pcs", position: 0 },
    { id: 2, name: "Assembly", quantity: "1.00", unit: "job", position: 1 },
  ],
  quotations: [
    {
      id: 10,
      supplier: "Complete Office",
      contact: "sales@example.com",
      validUntil: "2026-09-30",
      deliveryCost: "100.00",
      discount: "50.00",
      taxMode: "excluded",
      taxRate: "16.00",
      deliveryDays: 3,
      paymentTerms: "On delivery",
      preferred: false,
      prices: [
        { itemId: 1, unitPrice: "100.00" },
        { itemId: 2, unitPrice: "1000.00" },
      ],
      breakdown: { complete: true, coverage: 100, subtotal: "1200.00", deliveryCost: "100.00", tax: "192.00", discount: "50.00", total: "1442.00" },
    },
    {
      id: 11,
      supplier: "Cheap but incomplete",
      contact: null,
      validUntil: "2026-09-28",
      deliveryCost: "0.00",
      discount: "0.00",
      taxMode: "included",
      taxRate: "0.00",
      deliveryDays: null,
      paymentTerms: null,
      preferred: false,
      prices: [{ itemId: 1, unitPrice: "1.00" }],
      breakdown: { complete: false, coverage: 50, subtotal: "2.00", deliveryCost: "0.00", tax: "0.00", discount: "0.00", total: "2.00" },
    },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  api.get.mockResolvedValue({ data: [project] });
  api.post.mockResolvedValue({ data: { data: project } });
  api.patch.mockResolvedValue({ data: { data: project } });
  api.delete.mockResolvedValue({ data: { data: project } });
});

describe("Quotations", () => {
  it("ranks only complete offers and shows missing supplier prices honestly", async () => {
    render(<Quotations />);

    expect((await screen.findAllByText("Office chairs")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Lowest cost")).toHaveLength(1);
    expect(screen.getAllByText("50% priced").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Not supplied").length).toBeGreaterThan(0);
  });

  it("creates a persisted comparison through the authenticated API", async () => {
    const user = userEvent.setup();
    api.get.mockResolvedValue({ data: [] });
    render(<Quotations />);

    await screen.findByText("Make the next supplier choice with evidence");
    await user.click(screen.getByRole("button", { name: "Start a comparison" }));
    await user.type(screen.getByLabelText("What are you buying?"), "Solar panels");
    await user.type(screen.getByLabelText("Category"), "Energy");
    await user.click(screen.getByRole("button", { name: "Save comparison" }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      "/quotation-projects",
      expect.objectContaining({ title: "Solar panels", category: "Energy", currencyCode: "KES" }),
    ));
  });

  it("keeps lowest cost separate from the user's preferred supplier", async () => {
    const user = userEvent.setup();
    const selected = {
      ...project,
      status: "supplier_selected",
      preferredQuoteId: 11,
      quotations: project.quotations.map((quote) => ({ ...quote, preferred: quote.id === 11 })),
    };
    api.patch.mockResolvedValue({ data: { data: selected } });
    render(<Quotations />);

    const chooseButtons = await screen.findAllByRole("button", { name: "Choose supplier" });
    await user.click(chooseButtons[1]);

    expect(api.patch).toHaveBeenCalledWith(
      "/quotation-projects/41/quotes/11/preference",
      { preferred: true },
    );
    expect(await screen.findByText("Preferred")).toBeInTheDocument();
    expect(screen.getAllByText("Lowest cost")).toHaveLength(1);
  });

  it("offers common units and sends a user-defined custom unit", async () => {
    const user = userEvent.setup();
    render(<Quotations />);

    await screen.findAllByText("Office chairs");
    await user.click(screen.getByRole("button", { name: "Add item" }));
    await user.type(screen.getByLabelText("Item"), "Seedling tray");
    await user.selectOptions(screen.getByLabelText("Unit"), "custom");
    const customUnit = screen.getByLabelText("Custom unit");
    await user.type(customUnit, "trays");
    await user.click(within(customUnit.closest("form")).getByRole("button", { name: "Add item" }));

    expect(api.post).toHaveBeenCalledWith(
      "/quotation-projects/41/items",
      { name: "Seedling tray", quantity: "1", unit: "trays" },
    );
  });

  it("allows an existing item quantity to be corrected", async () => {
    const user = userEvent.setup();
    render(<Quotations />);

    await screen.findAllByText("Office chairs");
    await user.click(screen.getByRole("button", { name: "Edit Chair" }));
    const quantity = screen.getByLabelText("Quantity");
    await user.clear(quantity);
    await user.type(quantity, "12");
    await user.click(screen.getByRole("button", { name: "Update item" }));

    expect(api.patch).toHaveBeenCalledWith(
      "/quotation-projects/41/items/1",
      { name: "Chair", quantity: "12", unit: "pcs" },
    );
  });

  it("opens one price panel for all existing suppliers after adding an item", async () => {
    const user = userEvent.setup();
    const withNewItem = {
      ...project,
      items: [
        ...project.items,
        { id: 3, name: "Footrest", quantity: "2.00", unit: "pcs", position: 2 },
      ],
      quotations: project.quotations.map((quote) => ({
        ...quote,
        breakdown: { ...quote.breakdown, complete: false, coverage: 67 },
      })),
    };
    const withPrices = {
      ...withNewItem,
      quotations: withNewItem.quotations.map((quote, index) => ({
        ...quote,
        prices: [...quote.prices, { itemId: 3, unitPrice: index ? "650.00" : "600.00" }],
      })),
    };
    api.post.mockResolvedValueOnce({ data: { data: withNewItem } });
    api.patch.mockResolvedValueOnce({ data: { data: withPrices } });
    render(<Quotations />);

    await screen.findAllByText("Office chairs");
    await user.click(screen.getByRole("button", { name: "Add item" }));
    await user.type(screen.getByLabelText("Item"), "Footrest");
    const quantity = screen.getByLabelText("Quantity");
    await user.clear(quantity);
    await user.type(quantity, "2");
    await user.click(within(quantity.closest("form")).getByRole("button", { name: "Add item" }));

    expect(await screen.findByText("Add Footrest prices")).toBeInTheDocument();
    await user.type(screen.getByLabelText("Complete Office unit price for Footrest"), "600");
    await user.type(screen.getByLabelText("Cheap but incomplete unit price for Footrest"), "650");
    await user.click(screen.getByRole("button", { name: "Save supplier prices" }));

    expect(api.patch).toHaveBeenCalledWith(
      "/quotation-projects/41/items/3/prices",
      {
        prices: [
          { quotationId: 10, unitPrice: "600" },
          { quotationId: 11, unitPrice: "650" },
        ],
      },
    );
  });

  it("keeps quote validity optional and makes extra costs discoverable", async () => {
    const user = userEvent.setup();
    render(<Quotations />);

    await screen.findAllByText("Office chairs");
    await user.click(screen.getByRole("button", { name: "Add supplier" }));
    expect(screen.getByLabelText("Valid until (optional)")).not.toBeRequired();
    expect(screen.queryByLabelText("Delivery cost")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Add delivery and other costs/i }));
    expect(screen.getByLabelText("Delivery cost")).toBeInTheDocument();
    expect(screen.getByLabelText("Tax treatment")).toBeInTheDocument();
  });
});

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import SubscriptionIcon from "./SubscriptionIcon";


describe("SubscriptionIcon", () => {
  it.each([
    ["Chat GPT Plus", "Open AI", "chatgpt"],
    ["Deployments", "Railway", "railway"],
    ["Electricity", "KPLC", "kenya-power"],
    ["Home internet", "Safaricom Home Fibre", "safaricom"],
    ["Streaming", "Viu.to", "viu-to"],
    ["Snapchat+", "Snapchat", "snapchat"],
    ["Blue check", "X Premium", "x"],
    ["Cloud storage", "iCloud+", "icloud"],
    ["Photo storage", "Google Photos", "google-photos"],
  ])("normalizes %s / %s to %s", (name, provider, expectedKey) => {
    const { container } = render(
      <SubscriptionIcon
        subscription={{ kind: "subscription", name, provider }}
      />,
    );

    expect(container.firstChild).toHaveAttribute("data-brand-key", expectedKey);
  });

  it("renders a maintained SVG path for a supported brand", () => {
    const { container } = render(
      <SubscriptionIcon
        subscription={{ kind: "subscription", name: "Vercel Pro" }}
      />,
    );

    expect(container.querySelector('[data-brand-key="vercel"] svg path'))
      .toBeInTheDocument();
  });

  it("renders the OpenAI mark for names written as Chat GPT", () => {
    const { container } = render(
      <SubscriptionIcon
        subscription={{ kind: "subscription", name: "Chat GPT Plus" }}
      />,
    );

    expect(container.querySelector('[data-brand-key="chatgpt"] svg path'))
      .toBeInTheDocument();
    expect(container.querySelector(".subscription-icon-label"))
      .not.toBeInTheDocument();
  });

  it("uses a generic icon when the service is unknown", () => {
    const { container } = render(
      <SubscriptionIcon
        subscription={{ kind: "subscription", name: "My local club" }}
      />,
    );

    expect(container.firstChild).toHaveAttribute("data-brand-key", "generic");
  });
});

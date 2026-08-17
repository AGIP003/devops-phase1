import { ReceiptText, Repeat2, Wifi, Zap } from "lucide-react";
import {
  normalizeSubscriptionBrand,
  resolveSubscriptionBrand,
} from "./subscriptionBrands";

function SubscriptionIcon({ subscription, small = false }) {
  const brand = resolveSubscriptionBrand(subscription);
  const key = brand?.key || "generic";
  const searchableName = normalizeSubscriptionBrand(
    `${subscription.provider || ""} ${subscription.name || ""}`,
  );
  const fallbackColors = subscription.kind === "bill"
    ? { backgroundColor: "#eef0dc", color: "#59652f" }
    : { backgroundColor: "#e8f2eb", color: "#287a4d" };
  const customColors = brand
    ? {
        backgroundColor: brand.backgroundColor,
        color: brand.color,
      }
    : subscription.brandColor
    ? {
        backgroundColor: subscription.brandColor,
        color: subscription.accentColor,
      }
    : fallbackColors;

  let fallbackIcon = <Repeat2 size={small ? 18 : 21} />;
  if (searchableName.includes("wifi") || searchableName.includes("internet")) {
    fallbackIcon = <Wifi size={small ? 18 : 21} />;
  } else if (
    searchableName.includes("electric")
    || searchableName.includes("power")
  ) {
    fallbackIcon = <Zap size={small ? 18 : 21} />;
  } else if (subscription.kind === "bill") {
    fallbackIcon = <ReceiptText size={small ? 18 : 21} />;
  }

  return (
    <span
      className={`subscription-icon ${brand ? "subscription-icon-brand" : ""} ${small ? "subscription-icon-small" : ""} subscription-icon-${key}`}
      data-brand-key={key}
      style={customColors}
      aria-hidden="true"
    >
      {brand?.icon && (
        <svg viewBox="0 0 24 24">
          <path d={brand.icon.path} fill="currentColor" />
        </svg>
      )}
      {brand?.label && <b className="subscription-icon-label">{brand.label}</b>}
      {!brand && fallbackIcon}
    </span>
  );
}

export default SubscriptionIcon;

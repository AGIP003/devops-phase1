import { ReceiptText, Repeat2, Wifi, Zap } from "lucide-react";

function NetflixMark() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6 3h4.1l7.9 18h-4.2L6 3Z" fill="#e50914" />
      <path d="M14 3h4v18h-4V3Z" fill="#b20710" />
      <path d="M6 3h4v18H6V3Z" fill="#e50914" />
    </svg>
  );
}

function SpotifyMark() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M7.1 9.4c3.5-1 7.5-.6 10.5 1.1M7.7 12.5c2.8-.8 6-.5 8.4.9M8.3 15.4c2-.5 4.2-.4 6 .6"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function FigmaMark() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="9" cy="6" r="3" fill="#f24e1e" />
      <circle cx="15" cy="6" r="3" fill="#ff7262" />
      <circle cx="9" cy="12" r="3" fill="#a259ff" />
      <circle cx="15" cy="12" r="3" fill="#1abcfe" />
      <circle cx="9" cy="18" r="3" fill="#0acf83" />
    </svg>
  );
}

const brandIcons = {
  netflix: NetflixMark,
  spotify: SpotifyMark,
  figma: FigmaMark,
};

function getSubscriptionKey(subscription) {
  return subscription.name.toLowerCase().replace(/\s+/g, "-");
}

function SubscriptionIcon({ subscription, small = false }) {
  const key = getSubscriptionKey(subscription);
  const BrandIcon = brandIcons[key];
  const isBrandIcon = Boolean(BrandIcon);
  const fallbackColors = subscription.kind === "bill"
    ? { backgroundColor: "#eef0dc", color: "#59652f" }
    : { backgroundColor: "#e8f2eb", color: "#287a4d" };
  const customColors = subscription.brandColor
    ? {
        backgroundColor: subscription.brandColor,
        color: subscription.accentColor,
      }
    : fallbackColors;

  let fallbackIcon = <Zap size={small ? 18 : 21} />;
  if (subscription.kind === "bill") {
    fallbackIcon = <ReceiptText size={small ? 18 : 21} />;
  } else if (subscription.kind === "subscription") {
    fallbackIcon = <Repeat2 size={small ? 18 : 21} />;
  } else if (key === "wifi") {
    fallbackIcon = <Wifi size={small ? 18 : 21} />;
  }

  return (
    <span
      className={`subscription-icon ${isBrandIcon ? "subscription-icon-brand" : ""} ${small ? "subscription-icon-small" : ""} subscription-icon-${key}`}
      style={isBrandIcon ? undefined : customColors}
      aria-hidden="true"
    >
      {BrandIcon ? <BrandIcon /> : fallbackIcon}
    </span>
  );
}

export default SubscriptionIcon;

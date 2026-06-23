import { CalendarClock, Plus } from "lucide-react";
import { getSortedSubscriptions, subscriptions } from "../data/mockFinanceFeatures";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";

const dateFormatter = new Intl.DateTimeFormat("en-KE", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

function daysUntil(dateValue) {
  const today = new Date("2026-06-24T00:00:00");
  const dueDate = new Date(`${dateValue}T00:00:00`);
  return Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));
}

function SubscriptionIcon({ subscription }) {
  return (
    <span
      className="subscription-icon"
      style={{
        backgroundColor: subscription.brandColor,
        color: subscription.accentColor,
      }}
      aria-hidden="true"
    >
      {subscription.iconLabel}
    </span>
  );
}

function Bills() {
  const { formatCurrency } = useAdjustedCurrency();
  const sortedSubscriptions = getSortedSubscriptions(subscriptions);
  const nextBill = sortedSubscriptions[0];
  const totalMonthly = subscriptions.reduce((sum, item) => sum + item.amount, 0);

  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div>
          <span className="coming-soon-pill">Mock subscriptions</span>
          <h1>Bills & Subscription</h1>
          <p>Track upcoming recurring payments from soonest due to farthest.</p>
        </div>
        <button type="button" className="feature-primary-button" disabled>
          <Plus size={17} aria-hidden="true" />
          Add bill
        </button>
      </div>

      <section className="feature-summary-grid">
        <div className="feature-summary-card">
          <span>Monthly Total</span>
          <strong>{formatCurrency(totalMonthly)}</strong>
          <small>{subscriptions.length} active subscriptions</small>
        </div>
        <div className="feature-summary-card">
          <span>Due Next</span>
          <strong>{nextBill.name}</strong>
          <small>{dateFormatter.format(new Date(nextBill.dueDate))}</small>
        </div>
        <div className="feature-summary-card">
          <span>Capture</span>
          <strong>Manual first</strong>
          <small>Parsing rules can come after backend support</small>
        </div>
      </section>

      <section className="subscription-card-large">
        <div className="subscription-card-header">
          <div>
            <h2>
              <CalendarClock size={18} aria-hidden="true" />
              Bill & Subscription
            </h2>
            <p>Sorted by nearest due date</p>
          </div>
        </div>

        <div className="subscription-list">
          {sortedSubscriptions.map((subscription) => {
            const remainingDays = daysUntil(subscription.dueDate);
            return (
              <article className="subscription-row" key={subscription.id}>
                <SubscriptionIcon subscription={subscription} />
                <div>
                  <h3>{subscription.name}</h3>
                  <p>
                    {dateFormatter.format(new Date(subscription.dueDate))}
                    {remainingDays >= 0 ? ` · in ${remainingDays} days` : " · overdue"}
                  </p>
                </div>
                <strong>{formatCurrency(subscription.amount)}</strong>
              </article>
            );
          })}
        </div>
      </section>
    </div>
  );
}

export default Bills;

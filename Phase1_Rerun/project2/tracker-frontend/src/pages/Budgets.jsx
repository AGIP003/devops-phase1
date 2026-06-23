import { ClipboardCheck, Plus } from "lucide-react";
import { useMemo, useState } from "react";
import { budgets, getBudgetTotal } from "../data/mockFinanceFeatures";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";

function Budgets() {
  const { formatCurrency } = useAdjustedCurrency();
  const [budgetList, setBudgetList] = useState(budgets);
  const activeBudget = budgetList[0];
  const plannedTotal = getBudgetTotal(activeBudget.items);
  const checkedTotal = getBudgetTotal(activeBudget.items.filter((item) => item.checked));
  const remaining = activeBudget.targetAmount - checkedTotal;
  const checkedCount = activeBudget.items.filter((item) => item.checked).length;

  const otherBudgets = useMemo(() => budgetList.slice(1), [budgetList]);

  function toggleItem(itemId) {
    setBudgetList((current) =>
      current.map((budget) => {
        if (budget.id !== activeBudget.id) return budget;
        return {
          ...budget,
          items: budget.items.map((item) =>
            item.id === itemId ? { ...item, checked: !item.checked } : item
          ),
        };
      })
    );
  }

  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div>
          <span className="coming-soon-pill">Mock budgets</span>
          <h1>Budgets</h1>
          <p>Build reusable shopping lists, tick items while buying, and compare against last spend.</p>
        </div>
        <button type="button" className="feature-primary-button" disabled>
          <Plus size={17} aria-hidden="true" />
          New budget
        </button>
      </div>

      <section className="feature-summary-grid">
        <div className="feature-summary-card">
          <span>Target</span>
          <strong>{formatCurrency(activeBudget.targetAmount)}</strong>
          <small>{activeBudget.name}</small>
        </div>
        <div className="feature-summary-card">
          <span>Checked Off</span>
          <strong>{formatCurrency(checkedTotal)}</strong>
          <small>{checkedCount} of {activeBudget.items.length} items</small>
        </div>
        <div className="feature-summary-card">
          <span>Remaining</span>
          <strong>{formatCurrency(remaining)}</strong>
          <small>Last spend: {formatCurrency(activeBudget.lastSpend)}</small>
        </div>
      </section>

      <div className="budget-layout">
        <section className="budget-list-card">
          <div className="subscription-card-header">
            <div>
              <h2>
                <ClipboardCheck size={18} aria-hidden="true" />
                {activeBudget.name}
              </h2>
              <p>Tick items as you shop. Completed items stay visible but crossed out.</p>
            </div>
          </div>

          <div className="budget-progress-track" aria-hidden="true">
            <span style={{ width: `${Math.min(100, Math.round((checkedTotal / activeBudget.targetAmount) * 100))}%` }} />
          </div>

          <div className="budget-checklist">
            {activeBudget.items.map((item) => (
              <label className={`budget-item ${item.checked ? "checked" : ""}`} key={item.id}>
                <input
                  type="checkbox"
                  checked={item.checked}
                  onChange={() => toggleItem(item.id)}
                />
                <span>{item.name}</span>
                <strong>{formatCurrency(item.estimatedAmount)}</strong>
              </label>
            ))}
          </div>
        </section>

        <aside className="budget-side-card">
          <h2>Saved Lists</h2>
          <div className="saved-budget-list">
            {otherBudgets.map((budget) => (
              <article className="saved-budget-row" key={budget.id}>
                <div>
                  <strong>{budget.name}</strong>
                  <small>{budget.category}</small>
                </div>
                <span>{formatCurrency(budget.targetAmount)}</span>
              </article>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}

export default Budgets;

import { ClipboardCheck, Pencil, Plus, RefreshCw, Trash2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import api from "../services/api";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";

const EMPTY_ITEM = { name: "", estimatedAmount: "" };

function getEmptyForm() {
  return {
    name: "",
    category: "",
    targetAmount: "",
    items: [{ ...EMPTY_ITEM }, { ...EMPTY_ITEM }, { ...EMPTY_ITEM }],
  };
}

function toCurrencyNumber(value) {
  const amount = Number(value);
  return Number.isFinite(amount) ? amount : 0;
}

function getBudgetTotal(items = []) {
  return items.reduce(
    (total, item) => total + toCurrencyNumber(item.estimatedAmount),
    0
  );
}

function Budgets() {
  const { formatCurrency } = useAdjustedCurrency();
  const [budgetList, setBudgetList] = useState([]);
  const [activeBudgetId, setActiveBudgetId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [savingItemId, setSavingItemId] = useState(null);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingBudgetId, setEditingBudgetId] = useState(null);
  const [formError, setFormError] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [deletingBudgetId, setDeletingBudgetId] = useState(null);
  const [form, setForm] = useState(getEmptyForm);
  const budgetFormRef = useRef(null);

  const activeBudget = useMemo(() => {
    if (!budgetList.length) return null;
    return budgetList.find((budget) => budget.id === activeBudgetId) || budgetList[0];
  }, [activeBudgetId, budgetList]);

  const checkedItems = activeBudget?.items.filter((item) => item.checked) || [];
  const checkedTotal = getBudgetTotal(checkedItems);
  const targetAmount = toCurrencyNumber(activeBudget?.targetAmount);
  const remaining = targetAmount - checkedTotal;
  const checkedCount = checkedItems.length;
  const progress = targetAmount > 0 ? Math.min(100, Math.round((checkedTotal / targetAmount) * 100)) : 0;

  const otherBudgets = useMemo(
    () => budgetList.filter((budget) => budget.id !== activeBudget?.id),
    [activeBudget?.id, budgetList]
  );

  const fetchBudgets = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/budgets");
      const userBudgets = Array.isArray(response.data) ? response.data : [];
      setBudgetList(userBudgets);
      setActiveBudgetId((currentId) => {
        if (userBudgets.some((budget) => budget.id === currentId)) return currentId;
        return userBudgets[0]?.id || null;
      });
    } catch (err) {
      setError(err.message || "Unable to load budgets");
      setBudgetList([]);
      setActiveBudgetId(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBudgets();
  }, [fetchBudgets]);

  useEffect(() => {
    if (!showForm) return;

    budgetFormRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, [editingBudgetId, showForm]);

  async function toggleItem(itemId) {
    if (!activeBudget) return;

    const currentItem = activeBudget.items.find((item) => item.id === itemId);
    if (!currentItem) return;

    const nextChecked = !currentItem.checked;
    setSavingItemId(itemId);
    setBudgetList((current) =>
      current.map((budget) => {
        if (budget.id !== activeBudget.id) return budget;
        return {
          ...budget,
          items: budget.items.map((item) =>
            item.id === itemId ? { ...item, checked: nextChecked } : item
          ),
        };
      })
    );

    try {
      const response = await api.patch(`/budget-items/${itemId}`, { checked: nextChecked });
      const savedItem = response.data?.data;
      if (savedItem) {
        setBudgetList((current) =>
          current.map((budget) => ({
            ...budget,
            items: budget.items.map((item) =>
              item.id === itemId ? { ...item, ...savedItem } : item
            ),
          }))
        );
      }
    } catch (err) {
      setError(err.message || "Unable to update budget item");
      setBudgetList((current) =>
        current.map((budget) => {
          if (budget.id !== activeBudget.id) return budget;
          return {
            ...budget,
            items: budget.items.map((item) =>
              item.id === itemId ? { ...item, checked: currentItem.checked } : item
            ),
          };
        })
      );
    } finally {
      setSavingItemId(null);
    }
  }

  function updateItem(index, field, value) {
    setForm((current) => ({
      ...current,
      items: current.items.map((item, itemIndex) =>
        itemIndex === index ? { ...item, [field]: value } : item
      ),
    }));
  }

  function addItemRow() {
    setForm((current) => ({
      ...current,
      items: [...current.items, { ...EMPTY_ITEM }],
    }));
  }

  function removeItemRow(index) {
    setForm((current) => {
      if (current.items.length <= 1) return current;
      return {
        ...current,
        items: current.items.filter((_, itemIndex) => itemIndex !== index),
      };
    });
  }

  function resetForm() {
    setForm(getEmptyForm());
    setEditingBudgetId(null);
    setFormError("");
    setShowForm(false);
  }

  function startCreateBudget() {
    setForm(getEmptyForm());
    setEditingBudgetId(null);
    setFormError("");
    setShowForm(true);
  }

  function startEditBudget(budget) {
    setForm({
      name: budget.name || "",
      category: budget.category || "",
      targetAmount: String(budget.targetAmount || ""),
      items: budget.items.length
        ? budget.items.map((item) => ({
            id: item.id,
            name: item.name || "",
            estimatedAmount: String(item.estimatedAmount || ""),
            checked: Boolean(item.checked),
          }))
        : [{ ...EMPTY_ITEM }],
    });
    setEditingBudgetId(budget.id);
    setFormError("");
    setShowForm(true);
  }

  async function saveBudget(event) {
    event.preventDefault();
    setFormError("");

    const cleanItems = form.items
      .map((item) => ({
        id: item.id,
        name: item.name.trim(),
        estimatedAmount: Number(item.estimatedAmount),
        checked: Boolean(item.checked),
      }))
      .filter((item) => item.name && Number.isFinite(item.estimatedAmount));

    if (!form.name.trim()) {
      setFormError("Budget name is required");
      return;
    }

    if (!cleanItems.length) {
      setFormError("Add at least one budget item");
      return;
    }

    setIsCreating(true);
    try {
      const payload = {
        name: form.name.trim(),
        category: form.category.trim() || "General",
        targetAmount: Number(form.targetAmount),
        items: cleanItems,
      };
      const response = editingBudgetId
        ? await api.put(`/budgets/${editingBudgetId}`, payload)
        : await api.post("/budgets", payload);
      const savedBudget = response.data?.data;
      if (savedBudget) {
        setBudgetList((current) => {
          if (editingBudgetId) {
            return current.map((budget) =>
              budget.id === savedBudget.id ? savedBudget : budget
            );
          }
          return [savedBudget, ...current];
        });
        setActiveBudgetId(savedBudget.id);
      }
      resetForm();
    } catch (err) {
      setFormError(err.message || "Unable to save budget");
    } finally {
      setIsCreating(false);
    }
  }

  async function deleteBudget(budgetId) {
    const budget = budgetList.find((item) => item.id === budgetId);
    if (!budget) return;

    const confirmed = window.confirm(`Delete "${budget.name}" budget?`);
    if (!confirmed) return;

    setDeletingBudgetId(budgetId);
    setError("");
    try {
      await api.delete(`/budgets/${budgetId}`);
      const nextBudgets = budgetList.filter((item) => item.id !== budgetId);
      setBudgetList(nextBudgets);
      setActiveBudgetId((currentId) => {
        if (currentId !== budgetId) return currentId;
        return nextBudgets[0]?.id || null;
      });
      if (editingBudgetId === budgetId) {
        resetForm();
      }
    } catch (err) {
      setError(err.message || "Unable to delete budget");
    } finally {
      setDeletingBudgetId(null);
    }
  }

  function renderBudgetForm(extraClassName = "") {
    return (
      <form
        className={`budget-list-card budget-create-form ${extraClassName}`.trim()}
        onSubmit={saveBudget}
        ref={budgetFormRef}
      >
        <div className="budget-form-grid">
          <label>
            <span>Name</span>
            <input
              type="text"
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="Monthly groceries"
            />
          </label>
          <label>
            <span>Category</span>
            <input
              type="text"
              value={form.category}
              onChange={(event) => setForm({ ...form, category: event.target.value })}
              placeholder="Food"
            />
          </label>
          <label>
            <span>Target</span>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={form.targetAmount}
              onChange={(event) => setForm({ ...form, targetAmount: event.target.value })}
              placeholder="8500"
            />
          </label>
        </div>

        <div className="budget-form-items">
          {form.items.map((item, index) => (
            <div className="budget-form-item" key={`budget-form-item-${index}`}>
              <input
                type="text"
                value={item.name}
                onChange={(event) => updateItem(index, "name", event.target.value)}
                placeholder="Item name"
              />
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={item.estimatedAmount}
                onChange={(event) => updateItem(index, "estimatedAmount", event.target.value)}
                placeholder="Estimate"
              />
              <button
                type="button"
                className="budget-remove-item-button"
                onClick={() => removeItemRow(index)}
                disabled={form.items.length <= 1}
                aria-label={`Remove item ${index + 1}`}
                title="Remove item"
              >
                <Trash2 size={15} aria-hidden="true" />
              </button>
            </div>
          ))}
        </div>

        {formError && <p className="transaction-form-message transaction-form-error">{formError}</p>}

        <div className="budget-form-actions">
          <button type="button" className="secondary-button" onClick={addItemRow}>
            Add item
          </button>
          <button type="button" className="secondary-button" onClick={resetForm}>
            Cancel
          </button>
          <button type="submit" className="feature-primary-button" disabled={isCreating}>
            {isCreating ? "Saving..." : editingBudgetId ? "Update budget" : "Save budget"}
          </button>
        </div>
      </form>
    );
  }

  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div>
          <span className="page-context-label">Plan before you spend</span>
          <h1>Budgets</h1>
          <p>Plan a purchase, tick items as you shop, and compare the result with what you expected to spend.</p>
        </div>
        <button
          type="button"
          className="feature-primary-button"
          onClick={startCreateBudget}
        >
          <Plus size={17} aria-hidden="true" />
          New budget
        </button>
      </div>

      {showForm && !editingBudgetId && renderBudgetForm()}

      {error && (
        <div className="transaction-form-message transaction-form-error">
          {error}
          <button type="button" onClick={fetchBudgets}>
            <RefreshCw size={15} aria-hidden="true" />
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <section className="budget-list-card">
          <div className="drawer-loading">Loading budgets...</div>
        </section>
      ) : !activeBudget ? (
        <section className="budget-list-card">
          <div className="empty-state">
            <ClipboardCheck size={34} aria-hidden="true" />
            <p className="empty-state-title">No budgets yet</p>
            <p className="empty-state-message">Create a budget list to start tracking planned spend.</p>
          </div>
        </section>
      ) : (
        <>
          <section className="feature-summary-grid">
            <div className="feature-summary-card">
              <span>Target</span>
              <strong>{formatCurrency(targetAmount)}</strong>
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
              <small>Last spend: {formatCurrency(activeBudget.lastSpend || 0)}</small>
            </div>
          </section>

          <div className="budget-layout">
            <div className="budget-main-column">
              <section className="budget-list-card">
                <div className="subscription-card-header">
                  <div>
                    <h2>
                      <ClipboardCheck size={18} aria-hidden="true" />
                      {activeBudget.name}
                    </h2>
                    <p>Tick items as you shop. Completed items stay visible but crossed out.</p>
                  </div>
                  <div className="budget-card-actions">
                    <button
                      type="button"
                      className="table-action-button table-action-edit"
                      onClick={() => startEditBudget(activeBudget)}
                      aria-label={`Edit ${activeBudget.name}`}
                      title="Edit budget"
                    >
                      <Pencil size={16} aria-hidden="true" />
                    </button>
                    <button
                      type="button"
                      className="table-action-button table-action-delete"
                      onClick={() => deleteBudget(activeBudget.id)}
                      disabled={deletingBudgetId === activeBudget.id}
                      aria-label={`Delete ${activeBudget.name}`}
                      title="Delete budget"
                    >
                      <Trash2 size={16} aria-hidden="true" />
                    </button>
                  </div>
                </div>

                <div className="budget-progress-track" aria-hidden="true">
                  <span style={{ width: `${progress}%` }} />
                </div>

                <div className="budget-checklist">
                  {activeBudget.items.map((item) => (
                    <label className={`budget-item ${item.checked ? "checked" : ""}`} key={item.id}>
                      <input
                        type="checkbox"
                        checked={item.checked}
                        disabled={savingItemId === item.id}
                        onChange={() => toggleItem(item.id)}
                      />
                      <span>{item.name}</span>
                      <strong>{formatCurrency(toCurrencyNumber(item.estimatedAmount))}</strong>
                    </label>
                  ))}
                </div>
              </section>

              {showForm && editingBudgetId === activeBudget.id && renderBudgetForm("budget-edit-form")}
            </div>

            <aside className="budget-side-card">
              <h2>Saved Lists</h2>
              <div className="saved-budget-list">
                {otherBudgets.length ? (
                  otherBudgets.map((budget) => (
                    <button
                      className="saved-budget-row saved-budget-button"
                      key={budget.id}
                      type="button"
                      onClick={() => setActiveBudgetId(budget.id)}
                    >
                      <div>
                        <strong>{budget.name}</strong>
                        <small>{budget.category}</small>
                      </div>
                      <span>{formatCurrency(toCurrencyNumber(budget.targetAmount))}</span>
                    </button>
                  ))
                ) : (
                  <p className="empty-state-message">No other saved lists yet.</p>
                )}
              </div>
            </aside>
          </div>
        </>
      )}
    </div>
  );
}

export default Budgets;

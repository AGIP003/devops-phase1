import {
  CalendarClock,
  ChevronDown,
  CircleDollarSign,
  Landmark,
  Plus,
  ReceiptText,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import api from "../services/api";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";
import InfoHint from "../components/ui/InfoHint";


const DEBT_COLORS = ["#6f7f3f", "#c2413b", "#2f8f5b", "#3b82f6", "#8b5cf6"];
const categories = [
  ["personal", "Personal debt"],
  ["mobile_loan", "Mobile loan"],
  ["bank", "Bank loan"],
  ["sacco", "SACCO loan"],
  ["bnpl", "BNPL / hire purchase"],
  ["employer", "Employer advance"],
  ["business", "Business debt"],
  ["other", "Other"],
];
const feeOptions = [
  ["processing", "Processing fee"],
  ["origination", "Origination fee"],
  ["late_payment", "Late-payment penalty"],
  ["insurance", "Insurance fee"],
  ["service", "Administration / service fee"],
  ["restructuring", "Restructuring fee"],
  ["legal_collection", "Legal / collection fee"],
  ["other", "Other"],
];
const frequencyOptions = [
  ["one_time", "One-time repayment"],
  ["daily", "Daily"],
  ["weekly", "Weekly"],
  ["monthly", "Monthly"],
];
const paymentMethods = [
  "m-pesa",
  "cash",
  "bank transfer",
  "airtel money",
  "debit card",
  "credit card",
];
const filterOptions = [
  ["all", "All"],
  ["i_owe", "I Owe"],
  ["owed_to_me", "Owed to Me"],
];

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function getEmptyDebtForm() {
  return {
    title: "",
    direction: "i_owe",
    category: "other",
    counterparty: "",
    trackingKind: "new",
    originalAmount: "",
    currentBalance: "",
    amountAlreadyRepaid: "0",
    openedOn: todayIso(),
    notes: "",
    hasInterest: false,
    statedInterestRate: "",
    interestPeriod: "annual",
    hasFees: false,
    selectedFees: [],
    customFeeName: "",
    hasSchedule: false,
    frequency: "one_time",
    intervalCount: "1",
    installmentAmount: "",
    nextDueDate: "",
    finalDueDate: "",
  };
}

function getEmptyEntryForm() {
  return {
    entryType: "repayment",
    amount: "",
    occurredOn: todayIso(),
    feeCategory: "processing",
    customFeeName: "",
    notes: "",
    createTransaction: false,
    paymentMethod: "m-pesa",
  };
}

function labelFor(options, value) {
  return options.find(([key]) => key === value)?.[1]
    || value?.replaceAll("_", " ")
    || "Not set";
}

function formatDate(value) {
  if (!value) return "Not set";
  return new Intl.DateTimeFormat("en-KE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

function DebtPulseLine({ progress }) {
  const safeProgress = Number.isFinite(progress)
    ? Math.min(100, Math.max(0, progress))
    : 0;
  const gradientId = `debtPulse${useId().replace(/:/g, "")}`;
  return (
    <div
      className="debt-pulse-line"
      style={{ "--debt-progress": `${safeProgress}%` }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 240 34" preserveAspectRatio="none">
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset={`${safeProgress}%`} stopColor="#22c55e" />
            <stop offset={`${safeProgress}%`} stopColor="#ef4444" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
        </defs>
        <path
          stroke={`url(#${gradientId})`}
          d="M2 20 H42 L51 10 L62 27 L75 14 L88 20 H126 L136 7 L150 29 L166 15 L180 20 H238"
        />
      </svg>
      <span className="debt-pulse-glow" />
    </div>
  );
}

function Debts() {
  const { formatCurrency } = useAdjustedCurrency();
  const [debts, setDebts] = useState([]);
  const [activeFilter, setActiveFilter] = useState("all");
  const [expandedDebtId, setExpandedDebtId] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [debtForm, setDebtForm] = useState(getEmptyDebtForm);
  const [entryForm, setEntryForm] = useState(getEmptyEntryForm);
  const [showEntryForm, setShowEntryForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [success, setSuccess] = useState("");
  const expandedCardRef = useRef(null);
  const createFormRef = useRef(null);

  const fetchDebts = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/debts");
      setDebts(Array.isArray(response.data) ? response.data : []);
    } catch (requestError) {
      setError(requestError.message || "Unable to load debts");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDebts();
  }, [fetchDebts]);

  useEffect(() => {
    if (!showCreateForm) return;
    if (typeof createFormRef.current?.scrollIntoView === "function") {
      createFormRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [showCreateForm]);

  useEffect(() => {
    if (expandedDebtId === null) return undefined;
    function handleOutsideClick(event) {
      if (expandedCardRef.current && !expandedCardRef.current.contains(event.target)) {
        setExpandedDebtId(null);
        setShowEntryForm(false);
      }
    }
    function handleEscape(event) {
      if (event.key === "Escape") {
        setExpandedDebtId(null);
        setShowEntryForm(false);
      }
    }
    document.addEventListener("pointerdown", handleOutsideClick);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("pointerdown", handleOutsideClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [expandedDebtId]);

  const filteredDebts = useMemo(() => (
    activeFilter === "all"
      ? debts
      : debts.filter((debt) => debt.direction === activeFilter)
  ), [activeFilter, debts]);

  const summary = useMemo(() => debts.reduce((totals, debt) => {
    const balance = Number(debt.currentBalance || 0);
    if (debt.direction === "i_owe") totals.youOwe += balance;
    if (debt.direction === "owed_to_me") totals.owedToYou += balance;
    totals.netPosition = totals.owedToYou - totals.youOwe;
    return totals;
  }, { youOwe: 0, owedToYou: 0, netPosition: 0 }), [debts]);

  const chartData = useMemo(() => filteredDebts.reduce((items, debt) => {
    const name = labelFor(categories, debt.category);
    const existing = items.find((item) => item.name === name);
    if (existing) existing.value += Number(debt.currentBalance || 0);
    else items.push({ name, value: Number(debt.currentBalance || 0) });
    return items;
  }, []), [filteredDebts]);

  function openCreateForm() {
    setDebtForm(getEmptyDebtForm());
    setFormError("");
    setSuccess("");
    setExpandedDebtId(null);
    setShowEntryForm(false);
    setShowCreateForm(true);
  }

  function formHasContent() {
    return debtForm.title.trim()
      || debtForm.counterparty.trim()
      || debtForm.notes.trim()
      || debtForm.originalAmount
      || debtForm.currentBalance
      || debtForm.selectedFees.length > 0;
  }

  function cancelCreateForm() {
    if (formHasContent() && !window.confirm("Discard this unsaved debt?")) return;
    setShowCreateForm(false);
    setFormError("");
    setDebtForm(getEmptyDebtForm());
  }

  function toggleFee(feeCategory) {
    setDebtForm((current) => ({
      ...current,
      selectedFees: current.selectedFees.includes(feeCategory)
        ? current.selectedFees.filter((item) => item !== feeCategory)
        : [...current.selectedFees, feeCategory],
    }));
  }

  async function saveDebt(event) {
    event.preventDefault();
    setFormError("");
    setSuccess("");

    if (!debtForm.title.trim()) {
      setFormError("Add a clear description such as Amina lunch advance");
      return;
    }
    if (debtForm.trackingKind === "new" && !debtForm.originalAmount) {
      setFormError("Original amount is required for a new debt");
      return;
    }
    if (debtForm.trackingKind === "existing" && !debtForm.currentBalance) {
      setFormError("Current outstanding balance is required for an existing debt");
      return;
    }
    if (debtForm.hasSchedule && !debtForm.nextDueDate) {
      setFormError("Add the next payment date or turn off the repayment schedule");
      return;
    }
    if (debtForm.selectedFees.includes("other") && !debtForm.customFeeName.trim()) {
      setFormError("Name the custom fee");
      return;
    }

    const payload = {
      title: debtForm.title.trim(),
      direction: debtForm.direction,
      category: debtForm.category,
      counterparty: debtForm.counterparty.trim() || null,
      trackingKind: debtForm.trackingKind,
      originalAmount: debtForm.originalAmount || null,
      currentBalance: debtForm.currentBalance || null,
      amountAlreadyRepaid: debtForm.amountAlreadyRepaid || "0",
      currencyCode: "KES",
      openedOn: debtForm.openedOn || null,
      notes: debtForm.notes.trim() || null,
      hasInterest: debtForm.hasInterest,
      statedInterestRate: debtForm.hasInterest
        ? debtForm.statedInterestRate || null
        : null,
      interestPeriod: debtForm.hasInterest ? debtForm.interestPeriod : null,
      feeTerms: debtForm.hasFees
        ? debtForm.selectedFees.map((feeCategory) => ({
            feeCategory,
            customFeeName: feeCategory === "other"
              ? debtForm.customFeeName.trim()
              : null,
          }))
        : [],
      schedule: debtForm.hasSchedule
        ? {
            frequency: debtForm.frequency,
            intervalCount: Number(debtForm.intervalCount || 1),
            installmentAmount: debtForm.installmentAmount || null,
            nextDueDate: debtForm.nextDueDate,
            finalDueDate: debtForm.finalDueDate || null,
          }
        : null,
    };

    setSaving(true);
    try {
      const response = await api.post("/debts", payload);
      const savedDebt = response.data?.data;
      if (savedDebt) setDebts((current) => [savedDebt, ...current]);
      setShowCreateForm(false);
      setDebtForm(getEmptyDebtForm());
      setSuccess("Debt saved. Open the card whenever you need the full details.");
    } catch (requestError) {
      setFormError(requestError.message || "Unable to save debt");
    } finally {
      setSaving(false);
    }
  }

  function toggleDebt(debtId) {
    setExpandedDebtId((current) => current === debtId ? null : debtId);
    setShowEntryForm(false);
    setEntryForm(getEmptyEntryForm());
  }

  async function saveEntry(event, debtId) {
    event.preventDefault();
    setFormError("");
    if (!entryForm.amount) {
      setFormError("Entry amount is required");
      return;
    }
    if (
      entryForm.entryType === "fee"
      && entryForm.feeCategory === "other"
      && !entryForm.customFeeName.trim()
    ) {
      setFormError("Name the custom fee");
      return;
    }

    setSaving(true);
    try {
      const response = await api.post(`/debts/${debtId}/entries`, {
        ...entryForm,
        feeCategory: entryForm.entryType === "fee" ? entryForm.feeCategory : null,
        customFeeName: (
          entryForm.entryType === "fee" && entryForm.feeCategory === "other"
            ? entryForm.customFeeName.trim()
            : null
        ),
        createTransaction: (
          entryForm.entryType === "repayment" && entryForm.createTransaction
        ),
      });
      const updatedDebt = response.data?.data;
      if (updatedDebt) {
        setDebts((current) => current.map((debt) => (
          debt.id === debtId ? updatedDebt : debt
        )));
      }
      setEntryForm(getEmptyEntryForm());
      setShowEntryForm(false);
      setSuccess("Debt activity recorded.");
    } catch (requestError) {
      setFormError(requestError.message || "Unable to record debt activity");
    } finally {
      setSaving(false);
    }
  }

  async function archiveDebt(debt) {
    if (!window.confirm(`Archive “${debt.title}”? Its history will be preserved.`)) return;
    setSaving(true);
    try {
      await api.delete(`/debts/${debt.id}`);
      setDebts((current) => current.filter((item) => item.id !== debt.id));
      setExpandedDebtId(null);
      setSuccess("Debt archived.");
    } catch (requestError) {
      setError(requestError.message || "Unable to archive debt");
    } finally {
      setSaving(false);
    }
  }

  function renderDebtDetails(debt) {
    return (
      <div className="debt-expanded-content" id={`debt-details-${debt.id}`}>
        <div className="debt-detail-grid">
          <div><small>Original amount</small><strong>{debt.originalAmount ? formatCurrency(Number(debt.originalAmount)) : "Not supplied"}</strong></div>
          <div><small>Paid so far</small><strong>{formatCurrency(Number(debt.paidAmount))}</strong></div>
          <div><small>Counterparty</small><strong>{debt.counterparty || "Not supplied"}</strong></div>
          <div><small>Interest</small><strong>{debt.hasInterest ? debt.statedInterestRate ? `${debt.statedInterestRate}% ${debt.interestPeriod || ""}` : "Applies · rate not supplied" : "None recorded"}</strong></div>
          <div><small>Next payment</small><strong>{formatDate(debt.schedule?.nextDueDate)}</strong></div>
          <div><small>Final payoff</small><strong>{formatDate(debt.schedule?.finalDueDate)}</strong></div>
        </div>

        {debt.feeTerms.length > 0 && (
          <div className="debt-detail-section">
            <h4>Declared fees</h4>
            <div className="debt-fee-pills">
              {debt.feeTerms.map((fee) => (
                <span key={fee.id}>
                  {fee.feeCategory === "other"
                    ? fee.customFeeName
                    : labelFor(feeOptions, fee.feeCategory)}
                </span>
              ))}
            </div>
          </div>
        )}
        {debt.notes && <div className="debt-detail-section"><h4>Notes</h4><p>{debt.notes}</p></div>}

        <div className="debt-detail-section">
          <div className="debt-section-title">
            <div>
              <h4>Activity</h4>
              <p>Repayments reduce the balance; reported interest and fees increase it.</p>
            </div>
            <button
              type="button"
              className="debt-secondary-button"
              onClick={() => {
                setShowEntryForm((current) => !current);
                setEntryForm(getEmptyEntryForm());
                setFormError("");
              }}
            >
              <Plus size={15} aria-hidden="true" /> Record activity
            </button>
          </div>
          {debt.entries.length === 0 ? (
            <p className="debt-muted-copy">No activity recorded since tracking began.</p>
          ) : (
            <div className="debt-entry-list">
              {debt.entries.map((entry) => {
                const decreases = ["repayment", "adjustment_decrease"].includes(entry.entryType);
                const entryLabels = [
                  ["repayment", "Repayment"],
                  ["interest", "Reported interest"],
                  ["adjustment_increase", "Balance increase"],
                  ["adjustment_decrease", "Balance decrease"],
                ];
                return (
                  <div className="debt-entry-row" key={entry.id}>
                    <span className={decreases ? "decrease" : "increase"}><CircleDollarSign size={16} aria-hidden="true" /></span>
                    <div>
                      <strong>{entry.entryType === "fee" ? labelFor(feeOptions, entry.feeCategory) : labelFor(entryLabels, entry.entryType)}</strong>
                      <small>{formatDate(entry.occurredOn)}{entry.transactionId ? " · Linked transaction" : ""}</small>
                    </div>
                    <b>{decreases ? "−" : "+"}{formatCurrency(Number(entry.amount))}</b>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {showEntryForm && renderEntryForm(debt)}

        <div className="debt-expanded-actions">
          <span><CalendarClock size={16} aria-hidden="true" /> Added via {debt.createdVia.replaceAll("_", " ")}</span>
          <button type="button" className="debt-danger-button" onClick={() => archiveDebt(debt)} disabled={saving}><Trash2 size={15} aria-hidden="true" /> Archive</button>
        </div>
      </div>
    );
  }

  function renderEntryForm(debt) {
    return (
      <form className="debt-entry-form" onSubmit={(event) => saveEntry(event, debt.id)}>
        <label className="debt-field">
          <span>Activity</span>
          <select value={entryForm.entryType} onChange={(event) => setEntryForm({ ...entryForm, entryType: event.target.value, createTransaction: false })}>
            <option value="repayment">Repayment</option>
            <option value="interest">Reported interest</option>
            <option value="fee">Fee charged</option>
            <option value="adjustment_increase">Balance increase</option>
            <option value="adjustment_decrease">Balance decrease</option>
          </select>
        </label>
        <label className="debt-field"><span>Amount</span><input type="number" min="0.01" step="0.01" value={entryForm.amount} onChange={(event) => setEntryForm({ ...entryForm, amount: event.target.value })} /></label>
        <label className="debt-field"><span>Date</span><input type="date" value={entryForm.occurredOn} onChange={(event) => setEntryForm({ ...entryForm, occurredOn: event.target.value })} /></label>
        {entryForm.entryType === "fee" && (
          <>
            <label className="debt-field"><span>Fee type</span><select value={entryForm.feeCategory} onChange={(event) => setEntryForm({ ...entryForm, feeCategory: event.target.value })}>{feeOptions.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
            {entryForm.feeCategory === "other" && <label className="debt-field"><span>Custom fee</span><input value={entryForm.customFeeName} onChange={(event) => setEntryForm({ ...entryForm, customFeeName: event.target.value })} /></label>}
          </>
        )}
        {entryForm.entryType === "repayment" && (
          <div className="debt-entry-link">
            <label className="debt-switch-row">
              <span><strong>Also add to Transactions</strong><small>Avoid this if the transaction was already imported.</small></span>
              <input type="checkbox" checked={entryForm.createTransaction} onChange={(event) => setEntryForm({ ...entryForm, createTransaction: event.target.checked })} />
            </label>
            {entryForm.createTransaction && (
              <label className="debt-field">
                <span>Payment method</span>
                <select value={entryForm.paymentMethod} onChange={(event) => setEntryForm({ ...entryForm, paymentMethod: event.target.value })}>
                  {paymentMethods.map((method) => <option value={method} key={method}>{method}</option>)}
                </select>
              </label>
            )}
          </div>
        )}
        <label className="debt-field debt-field-wide"><span>Notes <em>optional</em></span><input value={entryForm.notes} onChange={(event) => setEntryForm({ ...entryForm, notes: event.target.value })} /></label>
        {formError && <p className="debt-form-error debt-field-wide" role="alert">{formError}</p>}
        <div className="debt-form-actions debt-field-wide"><button type="button" className="debt-secondary-button" onClick={() => setShowEntryForm(false)}>Cancel</button><button type="submit" className="feature-primary-button" disabled={saving}>{saving ? "Saving…" : "Save activity"}</button></div>
      </form>
    );
  }

  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div>
          <span className="coming-soon-pill">Live debt tracker</span>
          <h1>Debts & Loans</h1>
          <p>Track what you owe, what people owe you, and every balance-changing event.</p>
        </div>
        <button type="button" className="feature-primary-button" onClick={openCreateForm}><Plus size={17} aria-hidden="true" /> Add debt</button>
      </div>

      {error && <p className="debt-page-message debt-page-error" role="alert">{error}</p>}
      {success && <p className="debt-page-message debt-page-success" role="status">{success}</p>}

      {showCreateForm && (
        <form className="debt-create-card" onSubmit={saveDebt} ref={createFormRef}>
          <div className="debt-form-heading">
            <div><span>New record</span><h2>Add a debt</h2><p>Start with the facts you know. Interest, fees and schedules are optional.</p></div>
            <button type="button" className="debt-icon-button" onClick={cancelCreateForm} aria-label="Close debt form"><X size={19} aria-hidden="true" /></button>
          </div>

          <div className="debt-choice-grid">
            <fieldset>
              <legend>Direction</legend>
              <div className="debt-segmented-control">
                {[["i_owe", "I owe"], ["owed_to_me", "Owed to me"]].map(([value, label]) => (
                  <label className={debtForm.direction === value ? "active" : ""} key={value}><input type="radio" name="direction" value={value} checked={debtForm.direction === value} onChange={(event) => setDebtForm({ ...debtForm, direction: event.target.value })} />{label}</label>
                ))}
              </div>
            </fieldset>
            <fieldset>
              <legend>When did tracking begin?</legend>
              <div className="debt-segmented-control">
                {[["new", "New debt"], ["existing", "Existing debt"]].map(([value, label]) => (
                  <label className={debtForm.trackingKind === value ? "active" : ""} key={value}><input type="radio" name="trackingKind" value={value} checked={debtForm.trackingKind === value} onChange={(event) => setDebtForm({ ...debtForm, trackingKind: event.target.value })} />{label}</label>
                ))}
              </div>
            </fieldset>
          </div>

          <div className="debt-form-grid">
            <label className="debt-field debt-field-wide"><span>Description <InfoHint label="debt description" text="Describe the obligation, such as Amina lunch advance, instead of entering only a person's name." /></span><input aria-label="Description" value={debtForm.title} onChange={(event) => setDebtForm({ ...debtForm, title: event.target.value })} placeholder="Amina lunch advance" maxLength="140" /><small>Use a description you will recognize later—not merely a person’s name.</small></label>
            <label className="debt-field"><span>Category</span><select value={debtForm.category} onChange={(event) => setDebtForm({ ...debtForm, category: event.target.value })}>{categories.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
            <label className="debt-field"><span>Counterparty <em>optional</em></span><input value={debtForm.counterparty} onChange={(event) => setDebtForm({ ...debtForm, counterparty: event.target.value })} placeholder="KCB M-PESA or Amina" /></label>
            {debtForm.trackingKind === "new" ? (
              <label className="debt-field"><span>Original amount</span><input type="number" min="0.01" step="0.01" value={debtForm.originalAmount} onChange={(event) => setDebtForm({ ...debtForm, originalAmount: event.target.value })} placeholder="10000" /></label>
            ) : (
              <>
                <label className="debt-field"><span>Current outstanding balance</span><input type="number" min="0.01" step="0.01" value={debtForm.currentBalance} onChange={(event) => setDebtForm({ ...debtForm, currentBalance: event.target.value })} placeholder="8000" /></label>
                <label className="debt-field"><span>Original amount <em>optional</em></span><input type="number" min="0.01" step="0.01" value={debtForm.originalAmount} onChange={(event) => setDebtForm({ ...debtForm, originalAmount: event.target.value })} placeholder="10000" /></label>
              </>
            )}
            <label className="debt-field"><span>Already repaid <InfoHint label="amount already repaid" text="Money paid before you began tracking this debt. It establishes accurate starting progress." /></span><input aria-label="Already repaid" type="number" min="0" step="0.01" value={debtForm.amountAlreadyRepaid} onChange={(event) => setDebtForm({ ...debtForm, amountAlreadyRepaid: event.target.value })} /></label>
            <label className="debt-field"><span>{debtForm.trackingKind === "new" ? "Borrowed / lent on" : "Tracking from"}</span><input type="date" value={debtForm.openedOn} onChange={(event) => setDebtForm({ ...debtForm, openedOn: event.target.value })} /></label>
          </div>

          <div className="debt-optional-grid">
            <section className={`debt-option-panel ${debtForm.hasInterest ? "active" : ""}`}>
              <label className="debt-switch-row"><span><strong>Interest <InfoHint label="debt interest" text="Record the lender's stated rate only. MoneyTiq does not estimate or compound interest in this version." /></strong><small>Record only what the lender reports</small></span><input aria-label="Interest" type="checkbox" checked={debtForm.hasInterest} onChange={(event) => setDebtForm({ ...debtForm, hasInterest: event.target.checked })} /></label>
              {debtForm.hasInterest && <div className="debt-inline-fields"><label className="debt-field"><span>Stated rate <em>optional</em></span><input type="number" min="0.0001" step="0.0001" value={debtForm.statedInterestRate} onChange={(event) => setDebtForm({ ...debtForm, statedInterestRate: event.target.value })} placeholder="8.8" /></label><label className="debt-field"><span>Rate period</span><select value={debtForm.interestPeriod} onChange={(event) => setDebtForm({ ...debtForm, interestPeriod: event.target.value })}><option value="annual">Annual</option><option value="monthly">Monthly</option><option value="fixed">Fixed loan cost</option><option value="other">Other</option></select></label></div>}
            </section>

            <section className={`debt-option-panel ${debtForm.hasFees ? "active" : ""}`}>
              <label className="debt-switch-row"><span><strong>Fees <InfoHint label="debt fees" text="Identify possible fee types here; record the actual charged amount later as debt activity." /></strong><small>Select only fees that apply</small></span><input aria-label="Fees" type="checkbox" checked={debtForm.hasFees} onChange={(event) => setDebtForm({ ...debtForm, hasFees: event.target.checked, selectedFees: event.target.checked ? debtForm.selectedFees : [] })} /></label>
              {debtForm.hasFees && <div className="debt-fee-options">{feeOptions.map(([value, label]) => <label key={value} className={debtForm.selectedFees.includes(value) ? "selected" : ""}><input type="checkbox" checked={debtForm.selectedFees.includes(value)} onChange={() => toggleFee(value)} />{label}</label>)}{debtForm.selectedFees.includes("other") && <input className="debt-custom-fee-input" value={debtForm.customFeeName} onChange={(event) => setDebtForm({ ...debtForm, customFeeName: event.target.value })} placeholder="Name the other fee" />}</div>}
            </section>

            <section className={`debt-option-panel debt-option-wide ${debtForm.hasSchedule ? "active" : ""}`}>
              <label className="debt-switch-row"><span><strong>Repayment schedule <InfoHint label="repayment schedule" text="Describes when payments are expected. It does not automatically create repayments or transactions." /></strong><small>Keep next payment and final payoff separate</small></span><input aria-label="Repayment schedule" type="checkbox" checked={debtForm.hasSchedule} onChange={(event) => setDebtForm({ ...debtForm, hasSchedule: event.target.checked })} /></label>
              {debtForm.hasSchedule && <div className="debt-form-grid debt-schedule-grid"><label className="debt-field"><span>Frequency</span><select value={debtForm.frequency} onChange={(event) => setDebtForm({ ...debtForm, frequency: event.target.value })}>{frequencyOptions.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label><label className="debt-field"><span>Every</span><input type="number" min="1" step="1" value={debtForm.intervalCount} onChange={(event) => setDebtForm({ ...debtForm, intervalCount: event.target.value })} /></label><label className="debt-field"><span>Instalment <em>optional</em></span><input type="number" min="0.01" step="0.01" value={debtForm.installmentAmount} onChange={(event) => setDebtForm({ ...debtForm, installmentAmount: event.target.value })} /></label><label className="debt-field"><span>Next payment</span><input type="date" value={debtForm.nextDueDate} onChange={(event) => setDebtForm({ ...debtForm, nextDueDate: event.target.value })} /></label><label className="debt-field"><span>Final payoff <em>optional</em></span><input type="date" value={debtForm.finalDueDate} onChange={(event) => setDebtForm({ ...debtForm, finalDueDate: event.target.value })} /></label></div>}
            </section>
          </div>

          <label className="debt-field debt-field-wide"><span>Notes <em>optional</em></span><textarea rows="3" value={debtForm.notes} onChange={(event) => setDebtForm({ ...debtForm, notes: event.target.value })} placeholder="Only store details you genuinely need." /></label>
          {formError && <p className="debt-form-error" role="alert">{formError}</p>}
          <div className="debt-form-actions"><button type="button" className="debt-secondary-button" onClick={cancelCreateForm}>Cancel</button><button type="submit" className="feature-primary-button" disabled={saving}>{saving ? "Saving…" : "Save debt"}</button></div>
        </form>
      )}

      <section className="feature-summary-grid">
        <div className="feature-summary-card debt-negative"><span>You Owe</span><strong>{formatCurrency(summary.youOwe)}</strong><small>Active recorded obligations</small></div>
        <div className="feature-summary-card debt-positive"><span>Owed to You</span><strong>{formatCurrency(summary.owedToYou)}</strong><small>Money expected back</small></div>
        <div className="feature-summary-card"><span>Net Position</span><strong>{formatCurrency(summary.netPosition)}</strong><small>{summary.netPosition < 0 ? "More owed than receivable" : "Receivables ahead"}</small></div>
      </section>

      <div className="debts-layout">
        <section className="debt-list-card">
          <div className="section-heading"><div><h2>Debt List</h2><p>{loading ? "Loading your debts…" : `${debts.length} ${debts.length === 1 ? "record" : "records"}`}</p></div></div>
          <div className="feature-tabs" role="tablist" aria-label="Debt filter">{filterOptions.map(([value, label]) => <button type="button" key={value} className={activeFilter === value ? "active" : ""} onClick={() => setActiveFilter(value)}>{label}</button>)}</div>

          {!loading && filteredDebts.length === 0 && <div className="debt-empty-state"><ReceiptText size={28} aria-hidden="true" /><h3>No debts in this view</h3><p>Add only what you need to track. MoneyTiq will keep the history organized.</p></div>}

          <div className="debt-list">
            {filteredDebts.map((debt) => {
              const expanded = debt.id === expandedDebtId;
              const progress = debt.progress ?? 0;
              return (
                <article className={`debt-row-card ${expanded ? "expanded" : ""}`} key={debt.id} ref={expanded ? expandedCardRef : null} data-expanded-debt={expanded || undefined}>
                  <button className="debt-card-summary" type="button" onClick={() => toggleDebt(debt.id)} aria-expanded={expanded} aria-controls={`debt-details-${debt.id}`}>
                    <div className="debt-row-main"><div className="debt-type-icon" aria-hidden="true"><Landmark size={18} /></div><div><h3>{debt.title}</h3><p>{labelFor(categories, debt.category)} · {debt.direction === "i_owe" ? "I owe" : "Owed to me"}</p></div></div>
                    <div className="debt-row-amount"><strong>{formatCurrency(Number(debt.currentBalance))}</strong><small>{debt.schedule ? `Due ${formatDate(debt.schedule.nextDueDate)}` : "No repayment date"}</small></div>
                    <ChevronDown className="debt-expand-chevron" size={19} aria-hidden="true" />
                    <div className="debt-progress-area"><DebtPulseLine progress={progress} /><small>{debt.progress === null ? "Progress starts from the recorded balance" : `${debt.progress}% repaid`}{debt.schedule ? ` · ${labelFor(frequencyOptions, debt.schedule.frequency)}` : ""}</small></div>
                  </button>
                  {expanded && renderDebtDetails(debt)}
                </article>
              );
            })}
          </div>
        </section>

        <aside className="chart-card debt-chart-card">
          <div className="chart-card-header"><h3>Debt Breakdown</h3><span className="chart-card-kicker">Live</span></div>
          {chartData.length ? (
            <>
              <ResponsiveContainer width="100%" height={250}><PieChart><Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={58} outerRadius={105} paddingAngle={2} cornerRadius={6}>{chartData.map((_, index) => <Cell key={index} fill={DEBT_COLORS[index % DEBT_COLORS.length]} />)}</Pie><Tooltip formatter={(value) => formatCurrency(Number(value))} /></PieChart></ResponsiveContainer>
              <div className="donut-legend">{chartData.map((item, index) => <div className="donut-legend-item" key={item.name}><span className="donut-legend-dot" style={{ backgroundColor: DEBT_COLORS[index % DEBT_COLORS.length] }} /><span className="donut-legend-name">{item.name}</span><span className="donut-legend-percent">{formatCurrency(item.value)}</span></div>)}</div>
            </>
          ) : (
            <div className="debt-chart-empty"><Landmark size={28} aria-hidden="true" /><p>Your breakdown will appear after you add a debt.</p></div>
          )}
        </aside>
      </div>
    </div>
  );
}

export default Debts;

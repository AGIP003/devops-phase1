import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Archive,
  CalendarClock,
  CheckCircle2,
  ChevronDown,
  FastForward,
  History,
  PauseCircle,
  Pencil,
  PlayCircle,
  Plus,
  ReceiptText,
  Repeat2,
  X,
} from "lucide-react";

import InfoHint from "../components/ui/InfoHint";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";
import api from "../services/api";
import EditPanel from "../components/ui/EditPanel";
import SubscriptionIcon from "../components/ui/SubscriptionIcon";


const frequencyLabels = {
  weekly: "Weekly",
  monthly: "Monthly",
  quarterly: "Quarterly",
  termly: "Every 4 months",
  yearly: "Yearly",
  custom: "Custom",
};

const dateFormatter = new Intl.DateTimeFormat("en-KE", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

function todayValue() {
  return new Date().toISOString().slice(0, 10);
}

function formatDate(value) {
  if (!value) return "Not set";
  return dateFormatter.format(new Date(`${value}T00:00:00`));
}

function daysUntil(value) {
  const today = new Date(`${todayValue()}T00:00:00`);
  const dueDate = new Date(`${value}T00:00:00`);
  return Math.ceil((dueDate - today) / 86_400_000);
}

function dueLabel(commitment) {
  if (commitment.status === "cancelled") return "Recurrence stopped";
  const days = daysUntil(commitment.nextDueDate);
  if (days < 0) return `${Math.abs(days)} ${Math.abs(days) === 1 ? "day" : "days"} overdue`;
  if (days === 0) return "Due today";
  return `Due in ${days} ${days === 1 ? "day" : "days"}`;
}

function emptyCommitmentForm() {
  return {
    kind: "bill",
    name: "",
    provider: "",
    category: "",
    amount: "",
    amountKind: "fixed",
    nextDueDate: "",
    frequency: "monthly",
    customIntervalDays: "",
    autoRenews: true,
    notes: "",
  };
}

function emptyCycleForm(amount = "") {
  return {
    resolution: "paid",
    actualAmount: amount,
    resolvedOn: todayValue(),
    notes: "",
  };
}

function commitmentPayload(form) {
  return {
    ...form,
    name: form.name.trim(),
    provider: form.provider.trim() || null,
    category: form.category.trim() || null,
    customIntervalDays: form.frequency === "custom"
      ? Number(form.customIntervalDays)
      : null,
    autoRenews: form.kind === "subscription" ? form.autoRenews : null,
    amountKind: form.kind === "subscription" ? "fixed" : form.amountKind,
    notes: form.notes.trim() || null,
    currencyCode: "KES",
  };
}

function monthlyEquivalent(commitment) {
  const amount = Number(commitment.amount || 0);
  const multipliers = {
    weekly: 52 / 12,
    monthly: 1,
    quarterly: 1 / 3,
    termly: 1 / 4,
    yearly: 1 / 12,
  };
  if (commitment.frequency === "custom") {
    return amount * (30 / Math.max(Number(commitment.customIntervalDays), 1));
  }
  return amount * (multipliers[commitment.frequency] || 0);
}

function Bills() {
  const { formatCurrency } = useAdjustedCurrency();
  const createFormRef = useRef(null);
  const expandedCardRef = useRef(null);
  const [commitments, setCommitments] = useState([]);
  const [activeFilter, setActiveFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [showCycleForm, setShowCycleForm] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [form, setForm] = useState(emptyCommitmentForm);
  const [cycleForm, setCycleForm] = useState(emptyCycleForm);
  const [editingCommitment, setEditingCommitment] = useState(null);
  const [editingOccurrence, setEditingOccurrence] = useState(null);
  const [editForm, setEditForm] = useState(emptyCommitmentForm);
  const [editCycleForm, setEditCycleForm] = useState(emptyCycleForm);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchCommitments = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/commitments");
      setCommitments(Array.isArray(response.data) ? response.data : []);
    } catch (requestError) {
      setError(requestError.message || "Unable to load bills and subscriptions");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCommitments();
  }, [fetchCommitments]);

  useEffect(() => {
    if (showCreateForm && typeof createFormRef.current?.scrollIntoView === "function") {
      createFormRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [showCreateForm]);

  useEffect(() => {
    if (expandedId === null) return undefined;
    function closeOutside(event) {
      if (expandedCardRef.current && !expandedCardRef.current.contains(event.target)) {
        setExpandedId(null);
        setShowCycleForm(false);
        setShowHistory(false);
      }
    }
    function closeWithEscape(event) {
      if (event.key === "Escape") {
        setExpandedId(null);
        setShowCycleForm(false);
        setShowHistory(false);
      }
    }
    document.addEventListener("pointerdown", closeOutside);
    document.addEventListener("keydown", closeWithEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOutside);
      document.removeEventListener("keydown", closeWithEscape);
    };
  }, [expandedId]);

  const visibleCommitments = useMemo(() => commitments
    .filter((item) => activeFilter === "all" || item.kind === activeFilter)
    .sort((a, b) => {
      if (a.status !== b.status) return a.status === "active" ? -1 : 1;
      return a.nextDueDate.localeCompare(b.nextDueDate);
    }), [activeFilter, commitments]);

  const summary = useMemo(() => {
    const active = commitments.filter((item) => item.status === "active");
    const next = [...active].sort((a, b) => a.nextDueDate.localeCompare(b.nextDueDate))[0];
    return {
      activeCount: active.length,
      monthly: active.reduce((total, item) => total + monthlyEquivalent(item), 0),
      next,
      overdue: active.filter((item) => item.overdue).length,
    };
  }, [commitments]);

  function openCreateForm() {
    setForm(emptyCommitmentForm());
    setExpandedId(null);
    setShowCycleForm(false);
    setShowHistory(false);
    setFormError("");
    setSuccess("");
    setShowCreateForm(true);
  }

  function cancelCreateForm() {
    setShowCreateForm(false);
    setForm(emptyCommitmentForm());
    setFormError("");
  }

  function changeKind(kind) {
    setForm((current) => ({
      ...current,
      kind,
      amountKind: kind === "subscription" ? "fixed" : current.amountKind,
      autoRenews: kind === "subscription" ? current.autoRenews : null,
    }));
  }

  async function saveCommitment(event) {
    event.preventDefault();
    setFormError("");
    setSuccess("");
    if (!form.name.trim() || !form.amount || !form.nextDueDate) {
      setFormError("Name, amount and next due date are required");
      return;
    }
    if (form.frequency === "custom" && !form.customIntervalDays) {
      setFormError("Enter how many days are in the custom cycle");
      return;
    }

    setSaving(true);
    try {
      const response = await api.post("/commitments", commitmentPayload(form));
      const saved = response.data?.data;
      if (saved) setCommitments((current) => [...current, saved]);
      setShowCreateForm(false);
      setForm(emptyCommitmentForm());
      setSuccess(`${saved?.kind === "subscription" ? "Subscription" : "Bill"} saved.`);
    } catch (requestError) {
      setFormError(requestError.message || "Unable to save this item");
    } finally {
      setSaving(false);
    }
  }

  function toggleCommitment(commitment) {
    setExpandedId((current) => current === commitment.id ? null : commitment.id);
    setShowCycleForm(false);
    setShowHistory(false);
    setCycleForm(emptyCycleForm(commitment.amount));
    setFormError("");
  }

  function openCycleForm(commitment, resolution) {
    setCycleForm({
      ...emptyCycleForm(commitment.amount),
      resolution,
      actualAmount: resolution === "paid" ? commitment.amount : "",
    });
    setFormError("");
    setShowCycleForm(true);
  }

  async function saveCycle(event, commitment) {
    event.preventDefault();
    setFormError("");
    if (cycleForm.resolution === "paid" && !cycleForm.actualAmount) {
      setFormError("Enter the amount that was paid");
      return;
    }

    setSaving(true);
    try {
      const response = await api.post(`/commitments/${commitment.id}/cycles`, {
        ...cycleForm,
        actualAmount: cycleForm.resolution === "paid"
          ? cycleForm.actualAmount
          : null,
        notes: cycleForm.notes.trim() || null,
      });
      const updated = response.data?.data;
      if (updated) {
        setCommitments((current) => current.map((item) => (
          item.id === updated.id ? updated : item
        )));
      }
      setShowCycleForm(false);
      setSuccess(cycleForm.resolution === "paid"
        ? "Payment recorded and the next due date advanced."
        : "Cycle skipped and the next due date advanced.");
    } catch (requestError) {
      setFormError(requestError.message || "Unable to record this cycle");
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(commitment) {
    const nextStatus = commitment.status === "active" ? "cancelled" : "active";
    setSaving(true);
    setError("");
    try {
      const response = await api.patch(`/commitments/${commitment.id}/status`, {
        status: nextStatus,
      });
      const updated = response.data?.data;
      if (updated) {
        setCommitments((current) => current.map((item) => (
          item.id === updated.id ? updated : item
        )));
      }
      setSuccess(nextStatus === "cancelled" ? "Recurrence stopped." : "Recurrence restored.");
    } catch (requestError) {
      setError(requestError.message || "Unable to change this item");
    } finally {
      setSaving(false);
    }
  }

  function openCommitmentEditor(commitment) {
    setEditForm({
      kind: commitment.kind,
      name: commitment.name,
      provider: commitment.provider || "",
      category: commitment.category || "",
      amount: commitment.amount,
      amountKind: commitment.amountKind,
      nextDueDate: commitment.nextDueDate,
      frequency: commitment.frequency,
      customIntervalDays: commitment.customIntervalDays || "",
      autoRenews: commitment.autoRenews ?? true,
      notes: commitment.notes || "",
    });
    setEditingOccurrence(null);
    setFormError("");
    setEditingCommitment(commitment);
  }

  function changeEditKind(kind) {
    setEditForm((current) => ({
      ...current,
      kind,
      amountKind: kind === "subscription" ? "fixed" : current.amountKind,
      autoRenews: kind === "subscription" ? (current.autoRenews ?? true) : null,
    }));
  }

  async function saveCommitmentChanges(event) {
    event.preventDefault();
    if (!editForm.name.trim() || !editForm.amount || !editForm.nextDueDate) {
      setFormError("Name, amount and next due date are required");
      return;
    }
    if (editForm.frequency === "custom" && !editForm.customIntervalDays) {
      setFormError("Enter how many days are in the custom cycle");
      return;
    }

    setSaving(true);
    setFormError("");
    try {
      const response = await api.patch(
        `/commitments/${editingCommitment.id}`,
        commitmentPayload(editForm),
      );
      const updated = response.data?.data;
      if (updated) {
        setCommitments((current) => current.map((item) => (
          item.id === updated.id ? updated : item
        )));
      }
      setEditingCommitment(null);
      setSuccess("Recurring payment details updated.");
    } catch (requestError) {
      setFormError(requestError.message || "Unable to update this item");
    } finally {
      setSaving(false);
    }
  }

  function openOccurrenceEditor(commitment, occurrence) {
    setEditCycleForm({
      resolution: occurrence.resolution,
      actualAmount: occurrence.actualAmount || "",
      resolvedOn: occurrence.resolvedOn,
      notes: occurrence.notes || "",
    });
    setEditingCommitment(null);
    setFormError("");
    setEditingOccurrence({ commitment, occurrence });
  }

  async function saveOccurrenceChanges(event) {
    event.preventDefault();
    if (editCycleForm.resolution === "paid" && !editCycleForm.actualAmount) {
      setFormError("Enter the amount that was paid");
      return;
    }

    setSaving(true);
    setFormError("");
    try {
      const { commitment, occurrence } = editingOccurrence;
      const response = await api.patch(
        `/commitments/${commitment.id}/cycles/${occurrence.id}`,
        {
          ...editCycleForm,
          actualAmount: editCycleForm.resolution === "paid"
            ? editCycleForm.actualAmount
            : null,
          notes: editCycleForm.notes.trim() || null,
        },
      );
      const updated = response.data?.data;
      if (updated) {
        setCommitments((current) => current.map((item) => (
          item.id === updated.id ? updated : item
        )));
      }
      setEditingOccurrence(null);
      setSuccess("Payment history corrected.");
    } catch (requestError) {
      setFormError(requestError.message || "Unable to correct payment history");
    } finally {
      setSaving(false);
    }
  }

  async function archiveCommitment(commitment) {
    if (!window.confirm(`Archive “${commitment.name}”? Its history will be preserved.`)) return;
    setSaving(true);
    try {
      await api.delete(`/commitments/${commitment.id}`);
      setCommitments((current) => current.filter((item) => item.id !== commitment.id));
      setExpandedId(null);
      setSuccess("Item archived.");
    } catch (requestError) {
      setError(requestError.message || "Unable to archive this item");
    } finally {
      setSaving(false);
    }
  }

  function renderCreateForm() {
    const subscription = form.kind === "subscription";
    return (
      <form className="debt-create-card commitment-create-card" onSubmit={saveCommitment} ref={createFormRef}>
        <div className="debt-form-heading">
          <div><span>Recurring plan</span><h2>Add a bill or subscription</h2><p>Only add payments you expect to monitor again. Ordinary purchases belong in transactions.</p></div>
          <button type="button" className="debt-icon-button" onClick={cancelCreateForm} aria-label="Close bill form"><X size={19} aria-hidden="true" /></button>
        </div>

        <fieldset className="commitment-kind-choice">
          <legend>What are you tracking?</legend>
          <div className="debt-segmented-control">
            <label className={form.kind === "bill" ? "active" : ""}><input type="radio" name="kind" checked={form.kind === "bill"} onChange={() => changeKind("bill")} /><ReceiptText size={17} aria-hidden="true" /> Bill</label>
            <label className={form.kind === "subscription" ? "active" : ""}><input type="radio" name="kind" checked={form.kind === "subscription"} onChange={() => changeKind("subscription")} /><Repeat2 size={17} aria-hidden="true" /> Subscription</label>
          </div>
        </fieldset>

        <div className="debt-form-grid">
          <label className="debt-field debt-field-wide"><span>{subscription ? "Service name" : "Bill description"}</span><input aria-label={subscription ? "Service name" : "Bill description"} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder={subscription ? "Spotify" : "Electricity"} maxLength="120" /></label>
          <label className="debt-field"><span>Provider <em>optional</em></span><input value={form.provider} onChange={(event) => setForm({ ...form, provider: event.target.value })} placeholder={subscription ? "Spotify" : "Kenya Power"} maxLength="120" /></label>
          <label className="debt-field"><span>Category <em>optional</em></span><input value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} placeholder={subscription ? "Music" : "Utilities"} maxLength="80" /></label>
          <label className="debt-field"><span>Expected amount <InfoHint label="expected amount" text="For a variable bill, enter the best amount you expect. You can record the actual amount when you pay." /></span><input aria-label="Expected amount" type="number" min="0.01" step="0.01" value={form.amount} onChange={(event) => setForm({ ...form, amount: event.target.value })} placeholder="2500" /></label>
          {!subscription && <label className="debt-field"><span>Amount type <InfoHint label="amount type" text="Fixed means the amount normally stays the same. Estimated means it may change, such as electricity usage." /></span><select aria-label="Amount type" value={form.amountKind} onChange={(event) => setForm({ ...form, amountKind: event.target.value })}><option value="fixed">Fixed</option><option value="estimated">Estimated</option></select></label>}
          <label className="debt-field"><span>Next due date <InfoHint label="next due date" text="This is the next payment you expect, not the date you first subscribed." /></span><input aria-label="Next due date" type="date" value={form.nextDueDate} onChange={(event) => setForm({ ...form, nextDueDate: event.target.value })} /></label>
          <label className="debt-field"><span>Frequency <InfoHint label="payment frequency" text="Termly is treated as every four calendar months. Custom lets you specify an exact number of days." /></span><select aria-label="Frequency" value={form.frequency} onChange={(event) => setForm({ ...form, frequency: event.target.value })}><option value="weekly">Weekly</option><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="termly">Termly (every 4 months)</option><option value="yearly">Yearly</option><option value="custom">Custom</option></select></label>
          {form.frequency === "custom" && <label className="debt-field"><span>Repeat every how many days?</span><input type="number" min="1" max="366" value={form.customIntervalDays} onChange={(event) => setForm({ ...form, customIntervalDays: event.target.value })} placeholder="14" /></label>}
          {subscription && <label className="debt-switch-row commitment-auto-renew"><span><strong>Renews automatically?</strong><small>Is the provider expected to charge or renew it without you taking action?</small></span><input type="checkbox" checked={form.autoRenews} onChange={(event) => setForm({ ...form, autoRenews: event.target.checked })} /></label>}
          <label className="debt-field debt-field-wide"><span>Notes <em>optional</em></span><textarea rows="3" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} placeholder="Account details or a reminder—never store a password or PIN" /></label>
        </div>
        {formError && <p className="debt-form-error" role="alert">{formError}</p>}
        <div className="debt-form-actions"><button type="button" className="debt-secondary-button" onClick={cancelCreateForm}>Cancel</button><button type="submit" className="feature-primary-button" disabled={saving}>{saving ? "Saving…" : `Save ${subscription ? "subscription" : "bill"}`}</button></div>
      </form>
    );
  }

  function renderCycleForm(commitment) {
    const paid = cycleForm.resolution === "paid";
    return (
      <form className="commitment-cycle-form" onSubmit={(event) => saveCycle(event, commitment)}>
        <div className="debt-segmented-control">
          <label className={paid ? "active" : ""}><input type="radio" name="resolution" checked={paid} onChange={() => setCycleForm({ ...cycleForm, resolution: "paid", actualAmount: commitment.amount })} /> Paid</label>
          <label className={!paid ? "active" : ""}><input type="radio" name="resolution" checked={!paid} onChange={() => setCycleForm({ ...cycleForm, resolution: "skipped", actualAmount: "" })} /> Skipped</label>
        </div>
        {paid && <label className="debt-field"><span>Actual amount paid</span><input type="number" min="0.01" step="0.01" value={cycleForm.actualAmount} onChange={(event) => setCycleForm({ ...cycleForm, actualAmount: event.target.value })} /></label>}
        <label className="debt-field"><span>{paid ? "Payment" : "Decision"} date</span><input type="date" value={cycleForm.resolvedOn} onChange={(event) => setCycleForm({ ...cycleForm, resolvedOn: event.target.value })} /></label>
        <label className="debt-field"><span>Note <em>optional</em></span><input value={cycleForm.notes} onChange={(event) => setCycleForm({ ...cycleForm, notes: event.target.value })} placeholder={paid ? "Paid by M-Pesa" : "Provider waived this cycle"} /></label>
        {formError && <p className="debt-form-error commitment-field-wide" role="alert">{formError}</p>}
        <div className="debt-form-actions commitment-field-wide"><button type="button" className="debt-secondary-button" onClick={() => setShowCycleForm(false)}>Cancel</button><button type="submit" className="feature-primary-button" disabled={saving}>{saving ? "Saving…" : paid ? "Record payment" : "Skip cycle"}</button></div>
      </form>
    );
  }

  function renderDetails(commitment) {
    const active = commitment.status === "active";
    return (
      <div className="commitment-expanded-content" id={`commitment-details-${commitment.id}`}>
        <div className="commitment-detail-grid">
          <div><small>Provider</small><strong>{commitment.provider || "Not recorded"}</strong></div>
          <div><small>Category</small><strong>{commitment.category || "Not recorded"}</strong></div>
          <div><small>Frequency</small><strong>{commitment.frequency === "custom" ? `Every ${commitment.customIntervalDays} days` : frequencyLabels[commitment.frequency]}</strong></div>
          <div><small>Amount</small><strong>{commitment.amountKind === "estimated" ? "Estimated" : "Fixed"}</strong></div>
          {commitment.kind === "subscription" && <div><small>Auto-renew</small><strong>{commitment.autoRenews ? "Yes" : "No"}</strong></div>}
          <div><small>Added through</small><strong>{commitment.createdVia.replaceAll("_", " ")}</strong></div>
        </div>
        {commitment.notes && <div className="goal-note"><strong>Notes</strong><p>{commitment.notes}</p></div>}

        <div className="commitment-actions">
          <button type="button" className="feature-primary-button" disabled={!active} onClick={() => openCycleForm(commitment, "paid")}><CheckCircle2 size={16} aria-hidden="true" /> Mark paid</button>
          <button type="button" className="debt-secondary-button" disabled={!active} onClick={() => openCycleForm(commitment, "skipped")}><FastForward size={16} aria-hidden="true" /> Skip cycle</button>
          <button type="button" className="debt-secondary-button" onClick={() => openCommitmentEditor(commitment)}><Pencil size={16} aria-hidden="true" /> Edit details</button>
          <button type="button" className="debt-secondary-button" onClick={() => setShowHistory((current) => !current)} aria-expanded={showHistory}><History size={16} aria-hidden="true" /> {showHistory ? "Hide history" : `History (${commitment.occurrences.length})`}</button>
        </div>

        {showCycleForm && renderCycleForm(commitment)}

        {showHistory && (
          <div className="commitment-history">
            {commitment.occurrences.length === 0 ? <p>No completed cycles yet.</p> : commitment.occurrences.map((occurrence) => (
              <div className="commitment-history-row" key={occurrence.id}>
                <span className={occurrence.resolution}>{occurrence.resolution === "paid" ? <CheckCircle2 size={16} /> : <FastForward size={16} />}</span>
                <div><strong>{occurrence.notes || (occurrence.resolution === "paid" ? "Payment recorded" : "Cycle skipped")}</strong><small>Due {formatDate(occurrence.dueDate)} · resolved {formatDate(occurrence.resolvedOn)}</small></div>
                <b>{occurrence.actualAmount ? formatCurrency(Number(occurrence.actualAmount)) : "Skipped"}</b>
                <button type="button" className="activity-edit-button" onClick={() => openOccurrenceEditor(commitment, occurrence)} aria-label={`Edit ${occurrence.notes || "payment history"}`}><Pencil size={15} aria-hidden="true" /></button>
              </div>
            ))}
          </div>
        )}

        <div className="commitment-lifecycle-row">
          <span>Stopping recurrence keeps the card and history. Archiving hides both from normal views.</span>
          <div>
            <button type="button" className="debt-secondary-button" onClick={() => changeStatus(commitment)} disabled={saving}>{active ? <PauseCircle size={15} /> : <PlayCircle size={15} />}{active ? "Stop recurrence" : "Reactivate"}</button>
            <button type="button" className="debt-danger-button" onClick={() => archiveCommitment(commitment)} disabled={saving}><Archive size={15} aria-hidden="true" /> Archive</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div><span className="page-context-label">Upcoming commitments</span><h1>Bills & Subscriptions</h1><p>See what is due next, record a payment, and stop a recurring cost without losing its history.</p></div>
        <button type="button" className="feature-primary-button" onClick={openCreateForm}><Plus size={17} aria-hidden="true" /> Add item</button>
      </div>

      {error && <p className="debt-page-message debt-page-error" role="alert">{error}</p>}
      {success && <p className="debt-page-message debt-page-success" role="status">{success}</p>}
      {showCreateForm && renderCreateForm()}

      <section className="feature-summary-grid commitment-summary-ledger">
        <div className="feature-summary-card commitment-due-next"><span>Due next</span><strong>{summary.next?.name || "Nothing due"}</strong><small>{summary.next ? formatDate(summary.next.nextDueDate) : "Add a bill or subscription"}</small></div>
        <div className="feature-summary-card"><span>Estimated monthly</span><strong>{formatCurrency(summary.monthly)}</strong><small>{summary.activeCount} active recurring {summary.activeCount === 1 ? "item" : "items"}</small></div>
        <div className={`feature-summary-card commitment-attention${summary.overdue ? " has-overdue" : ""}`}><span>Needs attention</span><strong>{summary.overdue}</strong><small>{summary.overdue === 1 ? "overdue item" : "overdue items"}</small></div>
      </section>

      <div className="commitment-filter-bar" aria-label="Filter recurring payments">
        {[["all", "All"], ["bill", "Bills"], ["subscription", "Subscriptions"]].map(([value, label]) => <button type="button" key={value} className={activeFilter === value ? "active" : ""} onClick={() => setActiveFilter(value)}>{label}</button>)}
      </div>

      {loading && <div className="goal-loading-card">Loading your recurring payments…</div>}
      {!loading && visibleCommitments.length === 0 && <div className="goal-empty-state"><CalendarClock size={30} aria-hidden="true" /><h2>No recurring items in this view</h2><p>Add a bill or subscription you want MoneyTiq to monitor.</p></div>}

      <section className="subscription-card-large commitment-ledger-card">
        <div className="subscription-card-header">
          <div><h2><CalendarClock size={18} aria-hidden="true" /> Bill & Subscription</h2><p>Sorted by nearest due date</p></div>
        </div>
        <div className="subscription-list commitment-list">
          {visibleCommitments.map((commitment) => {
          const expanded = commitment.id === expandedId;
          return (
            <article className={`commitment-card ${expanded ? "expanded" : ""} ${commitment.status === "cancelled" ? "cancelled" : ""}`} key={commitment.id} ref={expanded ? expandedCardRef : null}>
              <button type="button" className="commitment-summary" onClick={() => toggleCommitment(commitment)} aria-expanded={expanded} aria-controls={`commitment-details-${commitment.id}`}>
                <SubscriptionIcon subscription={commitment} />
                <div className="commitment-summary-copy"><span>{commitment.kind}{commitment.status === "cancelled" ? " · stopped" : commitment.overdue ? " · overdue" : ""}</span><h2>{commitment.name}</h2><p>{formatDate(commitment.nextDueDate)} · {dueLabel(commitment)}</p></div>
                <div className="commitment-summary-amount"><strong>{formatCurrency(Number(commitment.amount))}</strong><small>{commitment.amountKind === "estimated" ? "estimated" : frequencyLabels[commitment.frequency]?.toLowerCase() || "recurring"}</small></div>
                <ChevronDown className="commitment-chevron" size={19} aria-hidden="true" />
              </button>
              {expanded && renderDetails(commitment)}
            </article>
          );
          })}
        </div>
      </section>

      {editingCommitment && (
        <EditPanel
          error={formError}
          onClose={() => { setEditingCommitment(null); setFormError(""); }}
          onSubmit={saveCommitmentChanges}
          saving={saving}
          title={`Edit ${editingCommitment.name}`}
        >
          <div className="edit-panel-grid">
            <fieldset className="commitment-kind-choice edit-panel-wide">
              <legend>Type</legend>
              <div className="debt-segmented-control">
                <label className={editForm.kind === "bill" ? "active" : ""}><input type="radio" name="edit-kind" checked={editForm.kind === "bill"} onChange={() => changeEditKind("bill")} /><ReceiptText size={17} aria-hidden="true" /> Bill</label>
                <label className={editForm.kind === "subscription" ? "active" : ""}><input type="radio" name="edit-kind" checked={editForm.kind === "subscription"} onChange={() => changeEditKind("subscription")} /><Repeat2 size={17} aria-hidden="true" /> Subscription</label>
              </div>
            </fieldset>
            <label className="debt-field edit-panel-wide"><span>{editForm.kind === "subscription" ? "Service name" : "Bill description"}</span><input aria-label="Edit recurring payment name" value={editForm.name} onChange={(event) => setEditForm({ ...editForm, name: event.target.value })} maxLength="120" /></label>
            <label className="debt-field"><span>Provider <em>optional</em></span><input aria-label="Edit recurring payment provider" value={editForm.provider} onChange={(event) => setEditForm({ ...editForm, provider: event.target.value })} maxLength="120" /></label>
            <label className="debt-field"><span>Category <em>optional</em></span><input aria-label="Edit recurring payment category" value={editForm.category} onChange={(event) => setEditForm({ ...editForm, category: event.target.value })} maxLength="80" /></label>
            <label className="debt-field"><span>Expected amount</span><input aria-label="Edit recurring payment amount" type="number" min="0.01" step="0.01" value={editForm.amount} onChange={(event) => setEditForm({ ...editForm, amount: event.target.value })} /></label>
            {editForm.kind === "bill" && <label className="debt-field"><span>Amount type</span><select aria-label="Edit recurring amount type" value={editForm.amountKind} onChange={(event) => setEditForm({ ...editForm, amountKind: event.target.value })}><option value="fixed">Fixed</option><option value="estimated">Estimated</option></select></label>}
            <label className="debt-field"><span>Next due date</span><input aria-label="Edit next due date" type="date" value={editForm.nextDueDate} onChange={(event) => setEditForm({ ...editForm, nextDueDate: event.target.value })} /></label>
            <label className="debt-field"><span>Frequency</span><select aria-label="Edit recurring frequency" value={editForm.frequency} onChange={(event) => setEditForm({ ...editForm, frequency: event.target.value })}><option value="weekly">Weekly</option><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="termly">Termly (every 4 months)</option><option value="yearly">Yearly</option><option value="custom">Custom</option></select></label>
            {editForm.frequency === "custom" && <label className="debt-field"><span>Repeat every how many days?</span><input aria-label="Edit custom interval" type="number" min="1" max="366" value={editForm.customIntervalDays} onChange={(event) => setEditForm({ ...editForm, customIntervalDays: event.target.value })} /></label>}
            {editForm.kind === "subscription" && <label className="debt-switch-row edit-panel-wide"><span><strong>Renews automatically?</strong><small>Whether the provider normally renews it without another action</small></span><input aria-label="Edit auto renew" type="checkbox" checked={editForm.autoRenews} onChange={(event) => setEditForm({ ...editForm, autoRenews: event.target.checked })} /></label>}
            <label className="debt-field edit-panel-wide"><span>Notes <em>optional</em></span><textarea aria-label="Edit recurring payment notes" rows="4" value={editForm.notes} onChange={(event) => setEditForm({ ...editForm, notes: event.target.value })} /></label>
          </div>
        </EditPanel>
      )}

      {editingOccurrence && (
        <EditPanel
          error={formError}
          eyebrow="Correct history"
          onClose={() => { setEditingOccurrence(null); setFormError(""); }}
          onSubmit={saveOccurrenceChanges}
          saving={saving}
          title={`${editingOccurrence.commitment.name} payment`}
        >
          <div className="edit-panel-grid">
            <label className="debt-field"><span>Result</span><select aria-label="Edit payment result" value={editCycleForm.resolution} onChange={(event) => setEditCycleForm({ ...editCycleForm, resolution: event.target.value, actualAmount: event.target.value === "paid" ? editingOccurrence.occurrence.expectedAmount : "" })}><option value="paid">Paid</option><option value="skipped">Skipped</option></select></label>
            {editCycleForm.resolution === "paid" && <label className="debt-field"><span>Actual amount paid</span><input aria-label="Edit actual amount paid" type="number" min="0.01" step="0.01" value={editCycleForm.actualAmount} onChange={(event) => setEditCycleForm({ ...editCycleForm, actualAmount: event.target.value })} /></label>}
            <label className="debt-field"><span>{editCycleForm.resolution === "paid" ? "Payment" : "Decision"} date</span><input aria-label="Edit payment date" type="date" value={editCycleForm.resolvedOn} onChange={(event) => setEditCycleForm({ ...editCycleForm, resolvedOn: event.target.value })} /></label>
            <label className="debt-field edit-panel-wide"><span>Note <em>optional</em></span><input aria-label="Edit payment note" value={editCycleForm.notes} onChange={(event) => setEditCycleForm({ ...editCycleForm, notes: event.target.value })} /></label>
          </div>
        </EditPanel>
      )}
    </div>
  );
}

export default Bills;

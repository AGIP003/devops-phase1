import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ChevronDown,
  History,
  PiggyBank,
  Plus,
  Target,
  Trash2,
  TrendingUp,
  X,
} from "lucide-react";

import api from "../services/api";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";
import InfoHint from "../components/ui/InfoHint";


const GOAL_COLORS = ["#6f7f3f", "#2f8f5b", "#3b82f6", "#a16207", "#7c3aed"];
const frequencyLabels = {
  weekly: "week",
  fortnightly: "fortnight",
  monthly: "month",
};

const dateFormatter = new Intl.DateTimeFormat("en-KE", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

function todayValue() {
  return new Date().toISOString().slice(0, 10);
}

function emptyGoalForm() {
  return {
    name: "",
    targetAmount: "",
    currentSavings: "",
    targetDate: "",
    contributionFrequency: "monthly",
    notes: "",
  };
}

function emptyEntryForm() {
  return {
    entryType: "contribution",
    amount: "",
    occurredOn: todayValue(),
    notes: "",
  };
}

function formatDate(value) {
  if (!value) return "Not set";
  return dateFormatter.format(new Date(`${value}T00:00:00`));
}

function GoalProgressRing({ progress, color }) {
  return (
    <div
      className="goal-progress-ring"
      style={{ "--goal-progress": `${progress}%`, "--goal-color": color }}
      aria-label={`${progress}% saved`}
    >
      <span>{progress}%</span>
    </div>
  );
}

function Goals() {
  const { formatCurrency } = useAdjustedCurrency();
  const [goals, setGoals] = useState([]);
  const [expandedGoalId, setExpandedGoalId] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEntryForm, setShowEntryForm] = useState(false);
  const [showActivity, setShowActivity] = useState(false);
  const [goalForm, setGoalForm] = useState(emptyGoalForm);
  const [entryForm, setEntryForm] = useState(emptyEntryForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [success, setSuccess] = useState("");
  const expandedCardRef = useRef(null);
  const createFormRef = useRef(null);

  const fetchGoals = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/goals");
      setGoals(Array.isArray(response.data) ? response.data : []);
    } catch (requestError) {
      setError(requestError.message || "Unable to load savings goals");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGoals();
  }, [fetchGoals]);

  useEffect(() => {
    if (!showCreateForm) return;
    if (typeof createFormRef.current?.scrollIntoView === "function") {
      createFormRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [showCreateForm]);

  useEffect(() => {
    if (expandedGoalId === null) return undefined;
    function closeOutside(event) {
      if (expandedCardRef.current && !expandedCardRef.current.contains(event.target)) {
        setExpandedGoalId(null);
        setShowEntryForm(false);
        setShowActivity(false);
      }
    }
    function closeWithEscape(event) {
      if (event.key === "Escape") {
        setExpandedGoalId(null);
        setShowEntryForm(false);
        setShowActivity(false);
      }
    }
    document.addEventListener("pointerdown", closeOutside);
    document.addEventListener("keydown", closeWithEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOutside);
      document.removeEventListener("keydown", closeWithEscape);
    };
  }, [expandedGoalId]);

  const summary = useMemo(() => {
    const totals = goals.reduce((result, goal) => ({
      saved: result.saved + Number(goal.currentSavings || 0),
      target: result.target + Number(goal.targetAmount || 0),
      reached: result.reached + (goal.targetReached ? 1 : 0),
    }), { saved: 0, target: 0, reached: 0 });
    return {
      ...totals,
      progress: totals.target > 0
        ? Math.min(100, Math.round((totals.saved / totals.target) * 100))
        : 0,
    };
  }, [goals]);

  function openCreateForm() {
    setGoalForm(emptyGoalForm());
    setExpandedGoalId(null);
    setShowEntryForm(false);
    setShowActivity(false);
    setFormError("");
    setSuccess("");
    setShowCreateForm(true);
  }

  function cancelCreateForm() {
    setShowCreateForm(false);
    setGoalForm(emptyGoalForm());
    setFormError("");
  }

  async function saveGoal(event) {
    event.preventDefault();
    setFormError("");
    setSuccess("");
    if (!goalForm.name.trim()) {
      setFormError("Give the goal a name you will recognize later");
      return;
    }
    if (!goalForm.targetAmount) {
      setFormError("Target amount is required");
      return;
    }
    if (!goalForm.targetDate) {
      setFormError("Target date is required");
      return;
    }

    setSaving(true);
    try {
      const response = await api.post("/goals", {
        name: goalForm.name.trim(),
        targetAmount: goalForm.targetAmount,
        currentSavings: goalForm.currentSavings || "0",
        targetDate: goalForm.targetDate,
        contributionFrequency: goalForm.contributionFrequency,
        currencyCode: "KES",
        notes: goalForm.notes.trim() || null,
      });
      const savedGoal = response.data?.data;
      if (savedGoal) {
        setGoals((current) => [...current, savedGoal].sort((a, b) => (
          a.targetDate.localeCompare(b.targetDate)
        )));
      }
      setShowCreateForm(false);
      setGoalForm(emptyGoalForm());
      setSuccess("Goal saved. Open its card to update savings or view activity.");
    } catch (requestError) {
      setFormError(requestError.message || "Unable to save goal");
    } finally {
      setSaving(false);
    }
  }

  function toggleGoal(goalId) {
    setExpandedGoalId((current) => current === goalId ? null : goalId);
    setShowEntryForm(false);
    setShowActivity(false);
    setEntryForm(emptyEntryForm());
    setFormError("");
  }

  async function saveEntry(event, goalId) {
    event.preventDefault();
    setFormError("");
    if (!entryForm.amount) {
      setFormError("Amount is required");
      return;
    }

    setSaving(true);
    try {
      const response = await api.post(`/goals/${goalId}/entries`, entryForm);
      const updatedGoal = response.data?.data;
      if (updatedGoal) {
        setGoals((current) => current.map((goal) => (
          goal.id === goalId ? updatedGoal : goal
        )));
      }
      setEntryForm(emptyEntryForm());
      setShowEntryForm(false);
      setSuccess("Savings activity recorded.");
    } catch (requestError) {
      setFormError(requestError.message || "Unable to update savings");
    } finally {
      setSaving(false);
    }
  }

  async function archiveGoal(goal) {
    if (!window.confirm(`Archive “${goal.name}”? Its activity will be preserved.`)) return;
    setSaving(true);
    try {
      await api.delete(`/goals/${goal.id}`);
      setGoals((current) => current.filter((item) => item.id !== goal.id));
      setExpandedGoalId(null);
      setSuccess("Goal archived.");
    } catch (requestError) {
      setError(requestError.message || "Unable to archive goal");
    } finally {
      setSaving(false);
    }
  }

  function renderEntryForm(goal) {
    return (
      <form className="goal-entry-form" onSubmit={(event) => saveEntry(event, goal.id)}>
        <label className="debt-field">
          <span>Change</span>
          <select value={entryForm.entryType} onChange={(event) => setEntryForm({ ...entryForm, entryType: event.target.value })}>
            <option value="contribution">Money added</option>
            <option value="withdrawal">Money removed</option>
          </select>
        </label>
        <label className="debt-field"><span>Amount</span><input type="number" min="0.01" step="0.01" value={entryForm.amount} onChange={(event) => setEntryForm({ ...entryForm, amount: event.target.value })} /></label>
        <label className="debt-field"><span>Date</span><input type="date" value={entryForm.occurredOn} onChange={(event) => setEntryForm({ ...entryForm, occurredOn: event.target.value })} /></label>
        <label className="debt-field"><span>Note <em>optional</em></span><input value={entryForm.notes} onChange={(event) => setEntryForm({ ...entryForm, notes: event.target.value })} placeholder="Weekly saving" /></label>
        {formError && <p className="debt-form-error goal-field-wide" role="alert">{formError}</p>}
        <div className="debt-form-actions goal-field-wide"><button type="button" className="debt-secondary-button" onClick={() => setShowEntryForm(false)}>Cancel</button><button type="submit" className="feature-primary-button" disabled={saving}>{saving ? "Saving…" : "Save update"}</button></div>
      </form>
    );
  }

  function renderGoalDetails(goal) {
    return (
      <div className="goal-expanded-content" id={`goal-details-${goal.id}`}>
        <div className="goal-detail-grid">
          <div><small>Still needed</small><strong>{formatCurrency(Number(goal.remainingAmount))}</strong></div>
          <div><small>Saving rhythm</small><strong>Every {frequencyLabels[goal.contributionFrequency]}</strong></div>
          <div><small>Periods remaining</small><strong>{goal.remainingPeriods || "Target reached"}</strong></div>
          <div><small>Added through</small><strong>{goal.createdVia.replaceAll("_", " ")}</strong></div>
        </div>

        {goal.notes && <div className="goal-note"><strong>Notes</strong><p>{goal.notes}</p></div>}

        <div className="goal-expanded-actions">
          <button type="button" className="feature-primary-button" onClick={() => { setShowEntryForm((current) => !current); setFormError(""); }}><Plus size={15} aria-hidden="true" /> Update savings</button>
          <button type="button" className="debt-secondary-button" onClick={() => setShowActivity((current) => !current)} aria-expanded={showActivity}><History size={15} aria-hidden="true" /> {showActivity ? "Hide activity" : `View activity (${goal.entries.length})`}</button>
        </div>

        {showEntryForm && renderEntryForm(goal)}

        {showActivity && (
          <div className="goal-activity-panel">
            {goal.entries.length === 0 ? (
              <p>No savings activity recorded yet.</p>
            ) : goal.entries.map((entry) => {
              const removed = entry.entryType === "withdrawal";
              return (
                <div className="goal-activity-row" key={entry.id}>
                  <span className={removed ? "removed" : "added"}>{removed ? "−" : "+"}</span>
                  <div><strong>{entry.notes || (removed ? "Money removed" : "Money added")}</strong><small>{formatDate(entry.occurredOn)}</small></div>
                  <b>{removed ? "−" : "+"}{formatCurrency(Number(entry.amount))}</b>
                </div>
              );
            })}
          </div>
        )}

        <div className="goal-archive-row">
          <span>History stays available in the database after archiving.</span>
          <button type="button" className="debt-danger-button" onClick={() => archiveGoal(goal)} disabled={saving}><Trash2 size={15} aria-hidden="true" /> Archive</button>
        </div>
      </div>
    );
  }

  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div>
          <span className="coming-soon-pill">Live goal tracker</span>
          <h1>Savings Goals</h1>
          <p>Choose a target and rhythm. MoneyTiq recalculates what to save as your progress changes.</p>
        </div>
        <button type="button" className="feature-primary-button" onClick={openCreateForm}><Plus size={17} aria-hidden="true" /> Add goal</button>
      </div>

      {error && <p className="debt-page-message debt-page-error" role="alert">{error}</p>}
      {success && <p className="debt-page-message debt-page-success" role="status">{success}</p>}

      {showCreateForm && (
        <form className="debt-create-card goal-create-card" onSubmit={saveGoal} ref={createFormRef}>
          <div className="debt-form-heading">
            <div><span>New plan</span><h2>Add a savings goal</h2><p>Enter the destination, deadline and saving rhythm. The suggested amount is calculated for you.</p></div>
            <button type="button" className="debt-icon-button" onClick={cancelCreateForm} aria-label="Close goal form"><X size={19} aria-hidden="true" /></button>
          </div>
          <div className="debt-form-grid">
            <label className="debt-field debt-field-wide"><span>Goal name</span><input value={goalForm.name} onChange={(event) => setGoalForm({ ...goalForm, name: event.target.value })} placeholder="Emergency fund" maxLength="120" /></label>
            <label className="debt-field"><span>Target amount <InfoHint label="target amount" text="The total amount you want this goal to reach." /></span><input aria-label="Target amount" type="number" min="0.01" step="0.01" value={goalForm.targetAmount} onChange={(event) => setGoalForm({ ...goalForm, targetAmount: event.target.value })} placeholder="120000" /></label>
            <label className="debt-field"><span>Already saved <em>optional</em> <InfoHint label="already saved" text="Creates an opening savings entry so the amount remains explainable in activity." /></span><input aria-label="Already saved" type="number" min="0" step="0.01" value={goalForm.currentSavings} onChange={(event) => setGoalForm({ ...goalForm, currentSavings: event.target.value })} placeholder="20000" /></label>
            <label className="debt-field"><span>Target date <InfoHint label="target date" text="MoneyTiq uses this deadline to calculate the remaining saving periods." /></span><input aria-label="Target date" type="date" min={todayValue()} value={goalForm.targetDate} onChange={(event) => setGoalForm({ ...goalForm, targetDate: event.target.value })} /></label>
            <label className="debt-field"><span>Saving frequency <InfoHint label="saving frequency" text="Choose whether the suggested contribution is calculated per week, fortnight, or calendar month." /></span><select aria-label="Saving frequency" value={goalForm.contributionFrequency} onChange={(event) => setGoalForm({ ...goalForm, contributionFrequency: event.target.value })}><option value="weekly">Weekly</option><option value="fortnightly">Fortnightly</option><option value="monthly">Monthly</option></select></label>
            <label className="debt-field debt-field-wide"><span>Notes <em>optional</em></span><textarea rows="3" value={goalForm.notes} onChange={(event) => setGoalForm({ ...goalForm, notes: event.target.value })} placeholder="Why this goal matters or what the amount covers" /></label>
          </div>
          {formError && <p className="debt-form-error" role="alert">{formError}</p>}
          <div className="debt-form-actions"><button type="button" className="debt-secondary-button" onClick={cancelCreateForm}>Cancel</button><button type="submit" className="feature-primary-button" disabled={saving}>{saving ? "Saving…" : "Save goal"}</button></div>
        </form>
      )}

      <section className="feature-summary-grid">
        <div className="feature-summary-card"><span>Total Saved</span><strong>{formatCurrency(summary.saved)}</strong><small>{summary.progress}% of all targets</small></div>
        <div className="feature-summary-card"><span>Combined Target</span><strong>{formatCurrency(summary.target)}</strong><small>{goals.length} {goals.length === 1 ? "goal" : "goals"}</small></div>
        <div className="feature-summary-card"><span>Goals Reached</span><strong>{summary.reached}</strong><small>Progress comes from recorded savings</small></div>
      </section>

      {loading && <div className="goal-loading-card">Loading your goals…</div>}
      {!loading && goals.length === 0 && (
        <div className="goal-empty-state"><Target size={30} aria-hidden="true" /><h2>No savings goals yet</h2><p>Add a target and MoneyTiq will calculate a realistic saving rhythm.</p></div>
      )}

      <section className="goals-grid">
        {goals.map((goal, index) => {
          const expanded = goal.id === expandedGoalId;
          const color = GOAL_COLORS[index % GOAL_COLORS.length];
          return (
            <article className={`goal-card goal-live-card ${expanded ? "expanded" : ""}`} key={goal.id} ref={expanded ? expandedCardRef : null}>
              <button className="goal-card-summary" type="button" onClick={() => toggleGoal(goal.id)} aria-expanded={expanded} aria-controls={`goal-details-${goal.id}`}>
                <div className="goal-card-top">
                  <div><span className="goal-label">{goal.targetReached ? "Target reached" : goal.overdue ? "Needs attention" : "Goal"}</span><h2>{goal.name}</h2></div>
                  <GoalProgressRing progress={goal.progress} color={color} />
                </div>
                <div className="goal-progress-track" aria-hidden="true"><span style={{ width: `${goal.progress}%`, backgroundColor: color }} /></div>
                <div className="goal-money-row"><span>{formatCurrency(Number(goal.currentSavings))}</span><span>{formatCurrency(Number(goal.targetAmount))}</span></div>
                <div className="goal-meta-grid">
                  <div><small>Suggested per {frequencyLabels[goal.contributionFrequency]}</small><strong>{formatCurrency(Number(goal.suggestedContribution))}</strong></div>
                  <div><small>Target date</small><strong>{formatDate(goal.targetDate)}</strong></div>
                </div>
                <div className="goal-open-hint"><span><PiggyBank size={15} aria-hidden="true" /> {goal.entries.length} {goal.entries.length === 1 ? "activity" : "activities"}</span><ChevronDown size={18} aria-hidden="true" /></div>
              </button>
              {expanded && renderGoalDetails(goal)}
            </article>
          );
        })}
      </section>

      {!loading && goals.length > 0 && (
        <div className="goal-engineering-note"><TrendingUp size={18} aria-hidden="true" /><p>The suggested amount is guidance. MoneyTiq records only the savings you confirm.</p></div>
      )}
    </div>
  );
}

export default Goals;

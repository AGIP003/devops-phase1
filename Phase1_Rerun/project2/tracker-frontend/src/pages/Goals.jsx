import { Bell, Bot, Plus, Tag } from "lucide-react";
import { savingsGoals, getGoalProgress } from "../data/mockFinanceFeatures";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";

const dateFormatter = new Intl.DateTimeFormat("en-KE", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

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
  const currencyFormatter = { format: formatCurrency };
  const totalSaved = savingsGoals.reduce((sum, goal) => sum + goal.savedAmount, 0);
  const totalTarget = savingsGoals.reduce((sum, goal) => sum + goal.targetAmount, 0);
  const overallProgress = Math.round((totalSaved / totalTarget) * 100);

  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div>
          <span className="coming-soon-pill">Frontend preview</span>
          <h1>Savings Goals</h1>
          <p>Plan what you are saving for, then connect real transactions later.</p>
        </div>
        <button type="button" className="feature-primary-button" disabled>
          <Plus size={17} aria-hidden="true" />
          Add goal
        </button>
      </div>

      <section className="feature-summary-grid">
        <div className="feature-summary-card">
          <span>Total Saved</span>
          <strong>{currencyFormatter.format(totalSaved)}</strong>
          <small>{overallProgress}% of all goals</small>
        </div>
        <div className="feature-summary-card">
          <span>Target</span>
          <strong>{currencyFormatter.format(totalTarget)}</strong>
          <small>{savingsGoals.length} active goals</small>
        </div>
        <div className="feature-summary-card">
          <span>Next Step</span>
          <strong>Tag savings</strong>
          <small>Manual capture will come after backend support</small>
        </div>
      </section>

      <div className="goals-layout">
        <section className="goals-grid">
          {savingsGoals.map((goal) => {
            const progress = getGoalProgress(goal);
            return (
              <article className="goal-card" key={goal.id}>
                <div className="goal-card-top">
                  <div>
                    <span className="goal-label">Goal</span>
                    <h2>{goal.name}</h2>
                  </div>
                  <GoalProgressRing progress={progress} color={goal.color} />
                </div>

                <div className="goal-progress-track" aria-hidden="true">
                  <span style={{ width: `${progress}%`, backgroundColor: goal.color }} />
                </div>

                <div className="goal-money-row">
                  <span>{currencyFormatter.format(goal.savedAmount)}</span>
                  <span>{currencyFormatter.format(goal.targetAmount)}</span>
                </div>

                <div className="goal-meta-grid">
                  <div>
                    <small>Monthly target</small>
                    <strong>{currencyFormatter.format(goal.monthlyTarget)}</strong>
                  </div>
                  <div>
                    <small>Target date</small>
                    <strong>{dateFormatter.format(new Date(goal.deadline))}</strong>
                  </div>
                </div>

                <div className="feature-action-row">
                  <button type="button" disabled>
                    <Tag size={16} aria-hidden="true" />
                    Tag transaction
                  </button>
                  <button type="button" disabled>
                    <Bell size={16} aria-hidden="true" />
                    Set nudge
                  </button>
                </div>
              </article>
            );
          })}
        </section>

        <aside className="feature-note-card">
          <div className="feature-note-icon">
            <Bot size={20} aria-hidden="true" />
          </div>
          <h2>Capture idea</h2>
          <p>
            The app should not guess savings automatically. A safer flow is manual tagging plus a bot nudge when there is budget surplus.
          </p>
          <div className="nudge-preview">
            <span>Bot preview</span>
            <p>Add today&apos;s KES 650 surplus to iPhone 17 Pro Max?</p>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default Goals;

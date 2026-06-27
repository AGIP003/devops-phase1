import { AlertTriangle, CheckCircle2, HandCoins, Plus, Send, Vote } from "lucide-react";
import { chamaGroups, getChamaProgress } from "../data/mockFinanceFeatures";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";

const dateFormatter = new Intl.DateTimeFormat("en-KE", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

function ChamaMemberStatus({ member }) {
  const isPaid = member.status === "paid";
  return (
    <div className={`chama-member-row ${isPaid ? "is-paid" : "is-pending"}`}>
      <span>
        {isPaid ? <CheckCircle2 size={15} aria-hidden="true" /> : <AlertTriangle size={15} aria-hidden="true" />}
        {member.name}
      </span>
      <strong>{isPaid ? "Paid" : "Pending"}</strong>
      <small>{member.strikes} strikes</small>
    </div>
  );
}

function Chamas() {
  const { formatCurrency } = useAdjustedCurrency();
  const activeChama = chamaGroups[0];
  const totalPool = chamaGroups.reduce((sum, chama) => sum + chama.poolAmount, 0);
  const pendingMembers = chamaGroups.reduce((sum, chama) => sum + (chama.memberCount - chama.paidCount), 0);
  const progress = getChamaProgress(activeChama);

  return (
    <div className="feature-page">
      <div className="feature-page-header">
        <div>
          <span className="coming-soon-pill">Frontend mock</span>
          <h1>Chama Tracker</h1>
          <p>Track chama contributions, public status, reminders, voting, and release.</p>
        </div>
        <button type="button" className="feature-primary-button" disabled>
          <Plus size={17} aria-hidden="true" />
          New chama
        </button>
      </div>

      <section className="feature-summary-grid">
        <div className="feature-summary-card">
          <span>Total Pool</span>
          <strong>{formatCurrency(totalPool)}</strong>
          <small>{chamaGroups.length} active groups</small>
        </div>
        <div className="feature-summary-card debt-positive">
          <span>This Cycle</span>
          <strong>{progress}% paid</strong>
          <small>{activeChama.paidCount} of {activeChama.memberCount} members</small>
        </div>
        <div className="feature-summary-card debt-negative">
          <span>Pending</span>
          <strong>{pendingMembers}</strong>
          <small>Telegram nudges planned</small>
        </div>
      </section>

      <div className="chama-layout">
        <section className="chama-cycle-card">
          <div className="chama-card-header">
            <div>
              <span className="goal-label">{activeChama.type}</span>
              <h2>{activeChama.name}</h2>
              <p>Due {dateFormatter.format(new Date(activeChama.dueDate))} · {activeChama.paybillMode}</p>
            </div>
            <div className="chama-pot-icon" aria-hidden="true">
              <HandCoins size={24} />
            </div>
          </div>

          <div className="chama-pot-row">
            <div>
              <small>Collected</small>
              <strong>{formatCurrency(activeChama.poolAmount)}</strong>
            </div>
            <div>
              <small>Target</small>
              <strong>{formatCurrency(activeChama.targetAmount)}</strong>
            </div>
            <div>
              <small>Recipient</small>
              <strong>{activeChama.currentRecipient}</strong>
            </div>
          </div>

          <div className="chama-progress-track" aria-label={`${progress}% paid`}>
            <span style={{ width: `${progress}%` }} />
          </div>

          <div className="chama-member-list">
            {activeChama.members.map((member) => (
              <ChamaMemberStatus member={member} key={member.id} />
            ))}
          </div>
        </section>

        <aside className="chama-side-stack">
          <section className="chama-mini-card">
            <h2>
              <Vote size={18} aria-hidden="true" />
              Cycle Vote
            </h2>
            <p>Used when the group does not follow fixed rotation.</p>
            <div className="chama-vote-list">
              {activeChama.votes.map((vote) => (
                <div className="chama-vote-row" key={vote.name}>
                  <span>{vote.name}</span>
                  <strong>{vote.votes} votes</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="chama-mini-card">
            <h2>
              <Send size={18} aria-hidden="true" />
              Telegram Broadcast
            </h2>
            <p>Mock broadcast shows paid/pending status to the group for accountability.</p>
            <button type="button" className="preview-link-button" disabled>
              Broadcast status
            </button>
          </section>
        </aside>
      </div>
    </div>
  );
}

export default Chamas;

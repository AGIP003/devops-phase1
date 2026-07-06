import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  BadgePercent,
  CheckCircle2,
  ClipboardCheck,
  HandCoins,
  LayoutDashboard,
  MessageCircle,
  ShieldCheck,
} from 'lucide-react';

const highlights = [
  { label: 'Tracked this month', value: 'KES 142,450' },
  { label: 'Saved from goals', value: 'KES 36,000' },
  { label: 'Recurring bills', value: '8 active' },
];

const transactions = [
  { name: 'Rent deposit', category: 'Housing', amount: '-45,000' },
  { name: 'M-Pesa salary', category: 'Income', amount: '+120,000' },
  { name: 'Internet bill', category: 'Bills', amount: '-4,500' },
];

function Landing() {
  useEffect(() => {
    document.body.classList.add('public-screen');
    return () => document.body.classList.remove('public-screen');
  }, []);

  return (
    <main className="public-page landing-page">
      <nav className="public-nav" aria-label="Main navigation">
        <Link className="public-brand" to="/">
          <span className="brand-mark">F</span>
          <span>
            <strong>Finance</strong>
            <small>Tracker</small>
          </span>
        </Link>

        <div className="public-nav-actions">
          <Link className="public-link" to="/demo">Preview</Link>
          <Link className="public-button ghost" to="/login">Log in</Link>
        </div>
      </nav>

      <section className="landing-hero">
        <div className="landing-copy">
          <span className="public-kicker">Personal finance, built for real tracking</span>
          <h1>Know where your money went before the month is over.</h1>
          <p>
            Finance Tracker brings spending, goals, bills, debts, fees, and Telegram logging into one focused dashboard.
            Visitors can preview the app first, then sign in when they are ready to use real data.
          </p>

          <div className="landing-actions">
            <Link className="public-button primary" to="/demo">
              Preview the app <ArrowRight size={18} />
            </Link>
            <Link className="public-button secondary" to="/login">Log in</Link>
          </div>

          <div className="landing-proof">
            <span><CheckCircle2 size={17} /> Flask API</span>
            <span><CheckCircle2 size={17} /> PostgreSQL models</span>
            <span><CheckCircle2 size={17} /> Telegram workflow</span>
          </div>
        </div>

        <div className="landing-preview-panel" aria-label="Finance Tracker dashboard preview">
          <div className="preview-topbar">
            <div>
              <span>Monthly overview</span>
              <strong>July snapshot</strong>
            </div>
            <span className="preview-status">Live pattern</span>
          </div>

          <div className="preview-metrics">
            {highlights.map((item) => (
              <article key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </article>
            ))}
          </div>

          <div className="preview-chart">
            {[52, 76, 34, 64, 88, 58, 71].map((height, index) => (
              <span key={height} style={{ '--bar-height': `${height}%` }} aria-label={`Week ${index + 1}`} />
            ))}
          </div>

          <div className="preview-grid">
            <div className="preview-list">
              <div className="preview-card-heading">
                <strong>Recent activity</strong>
                <span>3 updates</span>
              </div>
              {transactions.map((transaction) => (
                <div className="preview-transaction" key={transaction.name}>
                  <span>
                    <strong>{transaction.name}</strong>
                    <small>{transaction.category}</small>
                  </span>
                  <b className={transaction.amount.startsWith('+') ? 'is-income' : 'is-expense'}>
                    {transaction.amount}
                  </b>
                </div>
              ))}
            </div>

            <div className="preview-bot-card">
              <MessageCircle size={20} />
              <strong>Telegram capture</strong>
              <p>/spend 1200 groceries</p>
              <span>Logged, categorized, and ready for review.</span>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-band" aria-label="How Finance Tracker helps">
        <article>
          <LayoutDashboard size={22} />
          <strong>See the whole month</strong>
          <p>Balances, income, spending, bills, and goals are grouped into a dashboard built for quick scanning.</p>
        </article>
        <article>
          <HandCoins size={22} />
          <strong>Track local money habits</strong>
          <p>Debts, chama mockups, fees, and recurring expenses make the app feel closer to everyday use.</p>
        </article>
        <article>
          <BadgePercent size={22} />
          <strong>Spot hidden costs</strong>
          <p>Fee and subscription views help users catch small repeated expenses before they become background noise.</p>
        </article>
      </section>

      <section className="landing-detail">
        <div>
          <span className="public-kicker">What happens after login</span>
          <h2>A working product flow, not a static portfolio screen.</h2>
          <p>
            The signed-in app already connects to a Flask backend, stores data in PostgreSQL, and includes a Telegram bot flow.
            The public preview shows the shape of that experience without forcing a new visitor to create credentials first.
          </p>
        </div>

        <div className="landing-checklist">
          <span><ClipboardCheck size={18} /> Add and review transactions</span>
          <span><ShieldCheck size={18} /> Authenticate protected dashboard routes</span>
          <span><MessageCircle size={18} /> Connect Telegram-assisted logging</span>
          <span><LayoutDashboard size={18} /> Compare goals, bills, debts, budgets, and fees</span>
        </div>
      </section>

      <section className="landing-final">
        <div>
          <h2>Try the product shape before signing in.</h2>
          <p>The preview is interactive sample data today. Later, it can point to the guest-user backend you build.</p>
        </div>
        <Link className="public-button primary" to="/demo">
          Open preview <ArrowRight size={18} />
        </Link>
      </section>
    </main>
  );
}

export default Landing;

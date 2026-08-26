import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  BadgePercent,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  HandCoins,
  LayoutDashboard,
  Plus,
  ReceiptText,
} from 'lucide-react';

const startingTransactions = [
  { id: 1, title: 'M-Pesa salary', category: 'Income', type: 'income', amount: 120000 },
  { id: 2, title: 'Rent', category: 'Housing', type: 'expense', amount: 45000 },
  { id: 3, title: 'Groceries', category: 'Food', type: 'expense', amount: 8200 },
  { id: 4, title: 'Client invoice', category: 'Income', type: 'income', amount: 24000 },
  { id: 5, title: 'Internet', category: 'Bills', type: 'expense', amount: 4500 },
];

const quickAdds = [
  { title: 'Lunch', category: 'Food', type: 'expense', amount: 650 },
  { title: 'Matatu', category: 'Transport', type: 'expense', amount: 180 },
  { title: 'Side gig', category: 'Income', type: 'income', amount: 3500 },
];

const demoTabs = [
  { key: 'overview', label: 'Overview', icon: LayoutDashboard },
  { key: 'transactions', label: 'Transactions', icon: ReceiptText },
  { key: 'goals', label: 'Goals', icon: ClipboardCheck },
  { key: 'fees', label: 'Fees', icon: BadgePercent },
];

function formatKes(value) {
  return `KES ${value.toLocaleString()}`;
}

function DemoPreview() {
  const [activeTab, setActiveTab] = useState('overview');
  const [transactions, setTransactions] = useState(startingTransactions);
  const [selectedMonth, setSelectedMonth] = useState('July');

  useEffect(() => {
    document.body.classList.add('public-screen');
    return () => document.body.classList.remove('public-screen');
  }, []);

  const totals = useMemo(() => {
    return transactions.reduce(
      (summary, transaction) => {
        summary[transaction.type] += transaction.amount;
        return summary;
      },
      { income: 0, expense: 0 }
    );
  }, [transactions]);

  const balance = totals.income - totals.expense;
  const goalProgress = Math.min(100, Math.round((balance / 100000) * 100));

  function addTransaction(item) {
    setTransactions((current) => [
      { ...item, id: Date.now() },
      ...current,
    ]);
    setActiveTab('transactions');
  }

  function resetDemo() {
    setTransactions(startingTransactions);
    setActiveTab('overview');
  }

  return (
    <main className="public-page demo-preview-page">
      <nav className="public-nav" aria-label="Demo navigation">
        <Link className="public-brand" to="/">
          <span className="brand-mark" aria-hidden="true">
            <HandCoins size={17} strokeWidth={2.2} />
          </span>
          <span>
            <strong>MoneyTiq</strong>
            <small>Preview</small>
          </span>
        </Link>

        <div className="public-nav-actions">
          <button className="public-button ghost" type="button" onClick={resetDemo}>Reset demo</button>
          <Link className="public-button primary" to="/login">Log in</Link>
        </div>
      </nav>

      <section className="demo-shell" aria-label="Interactive MoneyTiq preview">
        <aside className="demo-sidebar">
          <h1>See how MoneyTiq works before you sign in.</h1>
          <p>
            Add a few sample entries, switch views, and see how your money would feel inside the app.
          </p>

          <div className="demo-tabs">
            {demoTabs.map(({ key, label, icon: Icon }) => (
              <button
                className={activeTab === key ? 'is-active' : ''}
                key={key}
                type="button"
                onClick={() => setActiveTab(key)}
              >
                <Icon size={18} />
                {label}
              </button>
            ))}
          </div>

          <div className="demo-quick-add">
            <strong>Try quick logging</strong>
            {quickAdds.map((item) => (
              <button key={item.title} type="button" onClick={() => addTransaction(item)}>
                <Plus size={16} />
                {item.title}
              </button>
            ))}
          </div>
        </aside>

        <section className="demo-board">
          <header className="demo-board-header">
            <div>
              <h2>Sample money for {selectedMonth}</h2>
            </div>
            <label>
              <span>Month</span>
              <select value={selectedMonth} onChange={(event) => setSelectedMonth(event.target.value)}>
                <option>July</option>
                <option>August</option>
                <option>September</option>
              </select>
            </label>
          </header>

          <div className="demo-metrics">
            <article>
              <span>Income</span>
              <strong>{formatKes(totals.income)}</strong>
            </article>
            <article>
              <span>Spending</span>
              <strong>{formatKes(totals.expense)}</strong>
            </article>
            <article>
              <span>Available</span>
              <strong>{formatKes(balance)}</strong>
            </article>
          </div>

          {activeTab === 'overview' && (
            <div className="demo-panel-grid">
              <article className="demo-card demo-wide-card">
                <div className="preview-card-heading">
                  <strong>Goal progress</strong>
                  <span>{goalProgress}%</span>
                </div>
                <div className="demo-progress">
                  <span style={{ width: `${goalProgress}%` }} />
                </div>
                <p>Emergency fund target: KES 100,000. The preview updates when you add sample income or expenses.</p>
              </article>

              <article className="demo-card">
                <CalendarClock size={22} />
                <strong>Upcoming bills</strong>
                <p>Internet, rent, and chama contribution are grouped so a user can prepare before due dates.</p>
              </article>

              <article className="demo-card">
                <HandCoins size={22} />
                <strong>Debt watch</strong>
                <p>Small obligations stay visible beside the main dashboard instead of hiding in notes.</p>
              </article>
            </div>
          )}

          {activeTab === 'transactions' && (
            <div className="demo-table-card">
              <div className="preview-card-heading">
                <strong>Transactions</strong>
                <span>{transactions.length} records</span>
              </div>
              <div className="demo-table">
                {transactions.map((transaction) => (
                  <div className="demo-table-row" key={transaction.id}>
                    <span>
                      <strong>{transaction.title}</strong>
                      <small>{transaction.category}</small>
                    </span>
                    <b className={transaction.type === 'income' ? 'is-income' : 'is-expense'}>
                      {transaction.type === 'income' ? '+' : '-'}{formatKes(transaction.amount)}
                    </b>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'goals' && (
            <div className="demo-panel-grid">
              <article className="demo-card demo-wide-card">
                <ClipboardCheck size={22} />
                <strong>Emergency fund</strong>
                <p>{formatKes(balance)} available toward a KES 100,000 target.</p>
                <div className="demo-progress">
                  <span style={{ width: `${goalProgress}%` }} />
                </div>
              </article>
              <article className="demo-card">
                <CheckCircle2 size={22} />
                <strong>Rent buffer</strong>
                <p>Sample status: covered for this cycle.</p>
              </article>
            </div>
          )}

          {activeTab === 'fees' && (
            <div className="demo-panel-grid">
              <article className="demo-card">
                <BadgePercent size={22} />
                <strong>Mobile money fees</strong>
                <p>KES 420 estimated from sample activity.</p>
              </article>
              <article className="demo-card demo-wide-card">
                <strong>Why this matters</strong>
                <p>Users often underestimate repeated charges. A fee view makes those costs visible next to spending.</p>
              </article>
            </div>
          )}

          <footer className="demo-footer-cta">
            <span>Ready to use your own money entries?</span>
            <Link to="/login">
              Log in to start <ArrowRight size={17} />
            </Link>
          </footer>
        </section>
      </section>
    </main>
  );
}

export default DemoPreview;

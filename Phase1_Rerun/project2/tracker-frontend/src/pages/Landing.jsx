import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  BadgePercent,
  CalendarClock,
  CheckSquare,
  ClipboardCheck,
  Coins,
  FileText,
  HandCoins,
  Landmark,
  LayoutDashboard,
  LockKeyhole,
  PiggyBank,
  ReceiptText,
  Send,
  ShieldCheck,
} from 'lucide-react';

const heroMetrics = [
  { label: 'Income', value: 'KES 84,500', note: 'M-Pesa salary + side income' },
  { label: 'Spending', value: 'KES 52,300', note: '62% of monthly income' },
  { label: 'Available balance', value: 'KES 32,200', note: 'Across M-Pesa + bank' },
  { label: 'Budget remaining', value: 'KES 9,700', note: 'Groceries and bills left', progress: 62 },
];

const recentTransactions = [
  { name: 'M-Pesa salary', category: 'Income', amount: '+ KES 84,500', type: 'income' },
  { name: 'Rent', category: 'Housing', amount: '- KES 25,000', type: 'expense' },
  { name: 'Groceries', category: 'Naivas', amount: '- KES 1,200', type: 'expense' },
  { name: 'Matatu', category: 'Transport', amount: '- KES 120', type: 'expense' },
  { name: 'Internet', category: 'Safaricom Home', amount: '- KES 4,100', type: 'expense' },
];

const featureModules = [
  {
    title: 'Dashboard',
    icon: LayoutDashboard,
    copy: 'See income, spending, recent activity, and a simple chart as soon as you open the app.',
    preview: 'dashboard',
  },
  {
    title: 'Transactions',
    icon: ReceiptText,
    copy: 'Add, edit, or delete money entries with category, payment method, and income or expense type.',
    preview: 'transactions',
  },
  {
    title: 'Budgets',
    icon: ClipboardCheck,
    copy: 'Make shopping lists, tick off items, and see how much of the budget is still left.',
    preview: 'budgets',
  },
  {
    title: 'Goals',
    icon: PiggyBank,
    copy: 'Set a target amount and watch the progress bar move every time you save.',
    preview: 'goals',
  },
  {
    title: 'Debts',
    icon: Landmark,
    copy: 'Keep track of who you owe, what is left, and how much you have already paid back.',
    preview: 'debts',
  },
  {
    title: 'Bills',
    icon: CalendarClock,
    copy: 'Keep rent, internet, chama, and other repeat bills visible before they are due.',
    preview: 'bills',
  },
  {
    title: 'Forex',
    icon: Coins,
    copy: 'Check exchange rates and quick conversions when you are dealing with another currency.',
    preview: 'forex',
  },
  {
    title: 'Quotations',
    icon: FileText,
    copy: 'Compare prices from different suppliers before you decide who to pay.',
    preview: 'quotations',
  },
  {
    title: 'Chamas',
    icon: HandCoins,
    copy: 'Follow contribution cycles and see how much has been collected so far.',
    preview: 'chamas',
  },
  {
    title: 'Fees',
    icon: BadgePercent,
    copy: 'See mobile money and bank charges so small fees do not disappear in the background.',
    preview: 'fees',
  },
  {
    title: 'Telegram',
    icon: Send,
    copy: 'Link Telegram once, then add spending from chat when opening the app feels too slow.',
    preview: 'telegram',
  },
  {
    title: 'Account privacy',
    icon: LockKeyhole,
    copy: 'Your money entries stay in your account. Other users cannot open or change them.',
    preview: 'privacy',
  },
];

const steps = [
  {
    title: 'Log money',
    copy: 'Enter transactions in the app, or send a Telegram message like /add 1200 groceries.',
  },
  {
    title: 'Review the dashboard',
    copy: 'Income, spending, available balance, and budget remaining update the moment an entry lands.',
  },
  {
    title: 'Plan ahead',
    copy: 'Use budgets, goals, bills, debts, and fees to see what is due, what is left, and what is next.',
  },
];

function ModulePreview({ type }) {
  if (type === 'dashboard') {
    return (
      <div className="money-mini-dashboard">
        <span>In <strong>84,500</strong></span>
        <span>Out <strong>52,300</strong></span>
        <span>Left <strong>32,200</strong></span>
        <b>Groceries - Naivas <em>- KES 1,200</em></b>
      </div>
    );
  }

  if (type === 'transactions') {
    return (
      <div className="money-mini-transaction">
        <strong>Matatu fare <em>- KES 120</em></strong>
        <span><b>Transport</b><b>M-Pesa</b></span>
        <small>+ Add transaction</small>
      </div>
    );
  }

  if (type === 'budgets') {
    return (
      <div className="money-mini-list">
        <span><CheckSquare size={13} /> Unga - 2kg <b>210</b></span>
        <span><CheckSquare size={13} /> Milk - 4 packets <b>260</b></span>
        <span className="open"><i /> Cooking oil - 1L <b>420</b></span>
        <small>Target KES 3,500 <b>KES 2,610 left</b></small>
      </div>
    );
  }

  if (type === 'goals' || type === 'debts' || type === 'chamas') {
    const labels = {
      goals: ['Emergency fund', '38%', 'KES 45,600 of KES 120,000'],
      debts: ['Owed to Njeri', 'KES 6,000 left', 'KES 9,000 of 15,000 repaid'],
      chamas: ['Umoja Chama - Cycle 4 of 12', 'KES 2,000/mo', '9 of 12 members paid'],
    };
    const [title, tag, note] = labels[type];
    return (
      <div className="money-mini-progress">
        <strong>{title}<span>{tag}</span></strong>
        <div><span /></div>
        <small>{note}</small>
      </div>
    );
  }

  if (type === 'bills') {
    return (
      <div className="money-mini-rows">
        <span>Rent - due 1 Aug <b>Upcoming</b></span>
        <span>Internet - due 5 Jul <b className="paid">Paid</b></span>
        <span>Chama contribution - due 15 Jul <b>Upcoming</b></span>
      </div>
    );
  }

  if (type === 'forex') {
    return (
      <div className="money-mini-rates">
        <span>USD to KES <b>129.40</b></span>
        <span>GBP to KES <b>163.85</b></span>
        <small>$100 = KES 12,940 after conversion</small>
      </div>
    );
  }

  if (type === 'quotations') {
    return (
      <div className="money-mini-quote">
        <span>Sofa set - 3 quotes <b>Best</b></span>
        <strong>Ngara Furniture <em>KES 48,000</em></strong>
        <small>Kariokor Works <b>KES 55,500</b></small>
      </div>
    );
  }

  if (type === 'fees') {
    return (
      <div className="money-mini-fees">
        <span>M-Pesa send - KES 5,000 <b>Fee KES 57</b></span>
        <span>Bank transfer - KES 20,000 <b>Fee KES 44</b></span>
        <small>KES 612 spent on fees this month</small>
      </div>
    );
  }

  if (type === 'telegram') {
    return (
      <div className="money-mini-telegram">
        <span>@you_linked</span>
        <strong>/add 350 matatu</strong>
        <small>Logged to Transport - today 08:12</small>
      </div>
    );
  }

  return (
    <div className="money-mini-privacy">
      <span>you@moneytiq <b>248 entries</b></span>
      <span>Other users <b>No access</b></span>
      <small>Your budget, bills, and transactions stay separate.</small>
    </div>
  );
}

function Landing() {
  useEffect(() => {
    document.body.classList.add('public-screen');
    return () => document.body.classList.remove('public-screen');
  }, []);

  return (
    <main className="public-page landing-page money-landing-page">
      <nav className="public-nav money-public-nav" aria-label="Main navigation">
        <Link className="public-brand money-brand" to="/">
          <span className="brand-mark" aria-hidden="true">
            <HandCoins size={17} strokeWidth={2.2} />
          </span>
          <strong>MoneyTiq</strong>
        </Link>

        <div className="public-nav-actions">
          <Link className="public-button ghost" to="/login">Log in</Link>
          <Link className="public-button primary" to="/demo">Try the preview</Link>
        </div>
      </nav>

      <section className="money-hero">
        <div className="money-hero-copy">
          <span className="money-pill"><ShieldCheck size={13} /> Your money, one clear view</span>
          <h1>Track spending, budgets, bills, debts, goals, and fees in one place.</h1>
          <p>
            MoneyTiq helps you see what came in, what went out, what is due, and what is still safe to spend.
            Add entries in the app or from Telegram, and keep everything private to your account.
          </p>

          <div className="landing-actions money-hero-actions">
            <Link className="public-button primary" to="/demo">
              Try the preview <ArrowRight size={17} />
            </Link>
            <Link className="public-button secondary" to="/login">Log in</Link>
          </div>
        </div>

        <section className="money-dashboard-mock" aria-label="MoneyTiq dashboard preview">
          <header className="money-mock-header">
            <span><LayoutDashboard size={14} /> Dashboard - July 2026</span>
            <small>you@moneytiq - KES</small>
          </header>

          <div className="money-metric-grid">
            {heroMetrics.map((metric) => (
              <article className={metric.progress ? 'is-highlighted' : ''} key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
                <small>{metric.note}</small>
                {metric.progress && (
                  <div className="money-metric-progress" aria-hidden="true">
                    <span style={{ width: `${metric.progress}%` }} />
                  </div>
                )}
              </article>
            ))}
          </div>

          <div className="money-mock-grid">
            <div className="money-transactions-panel">
              <h2>Recent transactions</h2>
              {recentTransactions.map((transaction) => (
                <div className="money-transaction-row" key={transaction.name}>
                  <span>{transaction.name} - {transaction.category}</span>
                  <strong className={transaction.type === 'income' ? 'is-income' : 'is-expense'}>
                    {transaction.amount}
                  </strong>
                </div>
              ))}
            </div>

            <div className="money-side-stack">
              <article className="money-spend-panel">
                <h2>Spending by week</h2>
                <div className="money-bars" aria-hidden="true">
                  {[36, 62, 48, 74, 30].map((height, index) => (
                    <span className={index === 2 ? 'active' : ''} style={{ height: `${height}%` }} key={height} />
                  ))}
                </div>
                <small>Week 3 - KES 14,850 logged</small>
              </article>

              <article className="money-telegram-panel">
                <h2><Send size={14} /> Telegram</h2>
                <strong>/add 1200 groceries</strong>
                <small>Logged: KES 1,200 - Groceries</small>
              </article>
            </div>
          </div>
        </section>
      </section>

      <section className="money-modules-section">
        <div className="money-section-heading">
          <h2>Every module of the app, up front</h2>
          <p>See what is inside before you sign in. Each card shows the kind of screen you will use in the app.</p>
        </div>

        <div className="money-feature-grid">
          {featureModules.map(({ title, icon: Icon, copy, preview }) => (
            <article className="money-feature-card" key={title}>
              <h3><Icon size={16} /> {title}</h3>
              <p>{copy}</p>
              <ModulePreview type={preview} />
            </article>
          ))}
        </div>
      </section>

      <section className="money-how-section">
        <h2>How it works</h2>
        <div className="money-step-grid">
          {steps.map((step, index) => (
            <article className="money-step-card" key={step.title}>
              <span>{index + 1}</span>
              <div>
                <strong>{step.title}</strong>
                <p>{step.copy}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="money-final-cta">
        <h2>Try MoneyTiq before you sign in.</h2>
        <p>Click around with sample KES data and see how the dashboard, budgets, bills, and goals feel in use.</p>
        <div className="landing-actions">
          <Link className="public-button primary" to="/demo">Try the preview</Link>
          <Link className="public-button secondary" to="/login">Log in</Link>
        </div>
      </section>

      <footer className="money-footer">
        <Link className="public-brand money-brand" to="/">
          <span className="brand-mark" aria-hidden="true">
            <HandCoins size={17} strokeWidth={2.2} />
          </span>
          <strong>MoneyTiq</strong>
        </Link>
        <small>Telegram logging - private accounts - your money stays yours</small>
      </footer>
    </main>
  );
}

export default Landing;

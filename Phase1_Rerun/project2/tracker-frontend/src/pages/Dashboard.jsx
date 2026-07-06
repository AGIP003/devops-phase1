import { useEffect, useId, useRef, useState } from "react";
import { BadgePercent, ChevronDown, FileUp, HandCoins, PencilLine } from "lucide-react";
import api from '../services/api'
import { getToken, removeToken } from "../utils/auth";
import { useNavigate, useOutletContext } from "react-router-dom";

import AddTransactionForm from "../components/auth/AddTransactionForm";
import { useMemo, useCallback } from "react";
import ChartsSection, { MonthlyTrendChart } from "../components/ui/ChartsSection";

import SummaryCards from "../components/ui/SummaryCard";
import { chamaGroups, debts, feeEvents, getChamaProgress, getDebtProgress, getFeeSummary, getSortedSubscriptions, subscriptions } from "../data/mockFinanceFeatures";
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";
import { TelegramIcon } from "../components/ui/TelegramLinkPanel";

const TELEGRAM_BOT_LINK = "https://t.me/pesatiq_bot";

function getUsernameFromToken() {
    const token = getToken();
    if (!token) return '';
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.username || payload.email || 'User';
    } catch {
        return 'User';
    }
}

// Skeleton row for the div-based recent transactions list.
function RecentTransactionSkeleton() {
    return (
        <div className="recent-row recent-row-skeleton">
            <span className="recent-index recent-skeleton-block" />
            <span className="recent-description recent-skeleton-block" />
            <span className="recent-category recent-skeleton-block" />
            <span className="recent-date recent-skeleton-block" />
            <span className="recent-amount recent-skeleton-block" />
        </div>
    )
}

function DebtPulseLine({ progress }) {
    const gradientId = `dashboardDebtPulse${useId().replace(/:/g, "")}`;
    return (
        <div className="debt-pulse-line debt-pulse-line-compact" style={{ "--debt-progress": `${progress}%` }} aria-hidden="true">
            <svg viewBox="0 0 240 34" preserveAspectRatio="none">
                <defs>
                    <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#22c55e" />
                        <stop offset={`${progress}%`} stopColor="#22c55e" />
                        <stop offset={`${progress}%`} stopColor="#ef4444" />
                        <stop offset="100%" stopColor="#ef4444" />
                    </linearGradient>
                </defs>
                <path stroke={`url(#${gradientId})`} d="M2 20 H42 L51 10 L62 27 L75 14 L88 20 H126 L136 7 L150 29 L166 15 L180 20 H238" />
            </svg>
            <span className="debt-pulse-glow" />
        </div>
    )
}

function SubscriptionIcon({ subscription }) {
    return (
        <span
            className="subscription-icon subscription-icon-small"
            style={{
                backgroundColor: subscription.brandColor,
                color: subscription.accentColor,
            }}
            aria-hidden="true"
        >
            {subscription.iconLabel}
        </span>
    )
}

function Dashboard() {
    const navigate = useNavigate();
    const { toggleSidebar } = useOutletContext();
    const accountMenuRef = useRef(null);
    const addMenuRef = useRef(null);
    const addTransactionPanelRef = useRef(null);
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [showAddMenu, setShowAddMenu] = useState(false);
    const [error, setError] = useState('');
    const [filterType, setFilterType] = useState("all");
    const [showAccountMenu, setShowAccountMenu] = useState(false);
    const [sidePreview, setSidePreview] = useState("bills");
    const { formatCurrency } = useAdjustedCurrency();


    //Derived filtered list
    const filteredTransactions = useMemo(() => {
        return transactions.filter(transaction => {
            //Type filter
            if (filterType !== 'all' && transaction.type !== filterType) return false;
            return true;
        })
    }, [transactions, filterType]);

    //recent tables
    const recentTransactions = transactions.slice(0, 6);
    const debtPreview = debts.slice(0, 3);
    const subscriptionPreview = getSortedSubscriptions(subscriptions).slice(0, 5);
    const chamaPreview = chamaGroups[0];
    const feeSummary = getFeeSummary(feeEvents);

    //Date Formatter
    const dateFormatter = new Intl.DateTimeFormat('en-KE', {
        day: '2-digit',
        month: 'short',
        year: "numeric",
    });


    //Fetch transactions
    const fetchTransactions = useCallback(async () => {
        setLoading(true);
        setError(''); // reset the previous errors     
        try {
            const response = await api.get('/transactions');
            const data = Array.isArray(response.data) ? response.data : [];
            setTransactions(data);
            console.log('Transaction sample:', data[0]);
        } catch (error) {
            setError(error.message);
            setTransactions([]);
        } finally {
            setLoading(false);
        }
    }, []);
    useEffect(() => {
        fetchTransactions();
    }, [fetchTransactions])

    useEffect(() => {
        if (showForm && addTransactionPanelRef.current) {
            addTransactionPanelRef.current.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        }
    }, [showForm]);

    //useMemo catches the results and only computes when dependencies change
    //USED WHEN COMPUTING IS EXPENSIVE OR WANT GUARANTTEE IT ONLY RUNS ONCE
    const username = useMemo(() => getUsernameFromToken(), []);

    //summary cards
    const currencyFormatter = { format: formatCurrency };

    //Privacy feature
    const [hideAmounts, setHideAmounts] = useState(() => {
        return localStorage.getItem("hideAmounts") === "true";
    });
    //update from the value in localstorage
    function toggleHideAmounts() {
        setHideAmounts(prev => {
            const nextValue = !prev;
            localStorage.setItem("hideAmounts", String(nextValue));
            return nextValue;
        });
    }
    //Click outside to close the menu
    useEffect(() => {
        function handleClickOutside(e) {
            if (
                accountMenuRef.current &&
                !accountMenuRef.current.contains(e.target)
            ) {
                setShowAccountMenu(false);
            }
            if (
                addMenuRef.current &&
                !addMenuRef.current.contains(e.target)
            ) {
                setShowAddMenu(false);
            }
            if (
                showForm &&
                addTransactionPanelRef.current &&
                !addTransactionPanelRef.current.contains(e.target) &&
                addMenuRef.current &&
                !addMenuRef.current.contains(e.target)
            ) {
                setShowForm(false);
            }
        }

        document.addEventListener("mousedown", handleClickOutside);

        return () => {
            document.removeEventListener("mousedown", handleClickOutside)
        };
    }, [showForm]);

    return (
        <div className="dashboard-page">
            <div className="dashboard-header">
                <div className="add-menu-wrap dashboard-add-menu" ref={addMenuRef}>
                    <button
                        type="button"
                        className={`add-menu-trigger ${showForm ? "is-active" : ""}`}
                        onClick={() => setShowAddMenu(prev => !prev)}
                        aria-expanded={showAddMenu}
                        aria-haspopup="menu"
                    >
                        <span className="add-menu-label-full">Add Transaction</span>
                        <span className="add-menu-label-mobile">Add</span>
                        <ChevronDown size={16} aria-hidden="true" />
                    </button>
                    {showAddMenu && (
                        <div className="add-menu" role="menu">
                            <button
                                type="button"
                                role="menuitem"
                                onClick={() => {
                                    setShowForm(true);
                                    setShowAddMenu(false);
                                }}
                            >
                                <PencilLine size={16} aria-hidden="true" />
                                <span>Manual add</span>
                            </button>
                            <button type="button" role="menuitem" disabled>
                                <FileUp size={16} aria-hidden="true" />
                                <span>Import</span>
                                <small>Coming soon</small>
                            </button>
                            <a href={TELEGRAM_BOT_LINK} role="menuitem" target="_blank" rel="noreferrer">
                                <TelegramIcon size={16} />
                                <span>Telegram bot</span>
                            </a>
                        </div>
                    )}
                </div>
                <div className="dashboard-header-left">
                    <button type="button" className="icon-button" aria-label="Toggle sidebar" onClick={toggleSidebar}>
                        <span className="menu-icon" aria-hidden="true">
                            <span />
                            <span />
                            <span />
                        </span>
                    </button>
                    <div className="dashboard-welcome-copy">
                        <h1>Welcome, {username} </h1>
                        <p>Showing {filteredTransactions.length} of {transactions.length} transactions</p>
                    </div>
                </div>
                <div className="account-menu-wrap dashboard-profile-menu" ref={accountMenuRef}>
                    <button
                        type="button"
                        className="profile-button"
                        aria-label="Open user profile menu"
                        aria-haspopup="menu"
                        aria-expanded={showAccountMenu}
                        onClick={() => setShowAccountMenu(prev => !prev)}
                    >
                        <span className="profile-initial">{username.charAt(0).toUpperCase()}</span>
                    </button>

                    {showAccountMenu && (
                        <div className="account-menu" role="menu">
                            <p>Signed in as</p>
                            <strong>{username}</strong>
                            <button type="button" role="menuitem" onClick={() => { removeToken(); navigate('/'); }}>
                                Logout
                            </button>
                        </div>
                    )}
                </div>
            </div>
            <div className="dashboard-overview">
                {error && <div className="error-banner">{error}</div>}
                <SummaryCards
                    filteredTransactions={filteredTransactions}
                    hideAmounts={hideAmounts}
                    currencyFormatter={currencyFormatter}
                    toggleHideAmounts={toggleHideAmounts}
                />
                <div className="dashboard-charts-row">
                    <MonthlyTrendChart
                        transactions={filteredTransactions}
                        filterType={filterType}
                    />
                    <ChartsSection
                        transactions={filteredTransactions}
                        filterType={filterType}
                        setFilterType={setFilterType}
                        toggleHideAmounts={toggleHideAmounts}
                    />
                </div>
            </div>
            {showForm && (
                <div ref={addTransactionPanelRef}>
                    <AddTransactionForm onSuccess={() => {
                        fetchTransactions();
                        setShowForm(false);
                    }} />
                </div>
            )}
            <div className="dashboard-main-grid">
                <div className="dashboard-bills-recent">
                    <section className="recent-card">
                        <div className="section-heading">
                            <div>
                                <h2>Recent Transactions</h2>
                            </div>

                            <button
                                type="button"
                                onClick={() => navigate(`/transactions`)}
                                aria-label="View all transactions"
                            >
                                View all
                            </button>
                        </div>

                        <div className="recent-table-head">
                            <span>S/N</span>
                            <span>Description</span>
                            <span>Category</span>
                            <span>Date</span>
                            <span>Amount</span>
                        </div>



                        <div className="recent-list">
                            {loading ? (
                                [...Array(5)].map((_, i) => <RecentTransactionSkeleton key={i} />)
                            ) : recentTransactions.map((tx, index) => (
                                <div className="recent-row" key={tx.id}>
                                    <span className="recent-index">
                                        {String(index + 1)}
                                    </span>

                                    <span className="recent-description">{tx.description}</span>

                                    <span className="recent-category">{tx.category}</span>

                                    <span className="recent-date">
                                        {dateFormatter.format(new Date(tx.date))}
                                    </span>

                                    <span className={`recent-amount recent-amount-${tx.type}`}>
                                        {tx.type === 'expense' ? '-' : '+'}
                                        {currencyFormatter.format(Number(tx.amount || 0))}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </section>
                    <aside className="dashboard-side-stack">

                        <section className="bills-card">
                            <div className="section-heading">
                                <div>
                                    <h2>{sidePreview === "bills" ? "Bill & Subscription" : sidePreview === "debts" ? "Debt Preview" : sidePreview === "chamas" ? "Chama Cycle" : "Fees Watch"}</h2>
                                    <p>{sidePreview === "bills" ? "Upcoming recurring payments" : sidePreview === "debts" ? "Top balances from debt tracker" : sidePreview === "chamas" ? "Merry-go-round status mock" : "Estimated cost of moving money"}</p>
                                </div>
                                <div className="preview-switcher" aria-label="Switch dashboard preview">
                                    <button
                                        type="button"
                                        className={sidePreview === "bills" ? "active" : ""}
                                        onClick={() => setSidePreview("bills")}
                                    >
                                        Bills
                                    </button>
                                    <button
                                        type="button"
                                        className={sidePreview === "debts" ? "active" : ""}
                                        onClick={() => setSidePreview("debts")}
                                    >
                                        Debts
                                    </button>
                                    <button
                                        type="button"
                                        className={sidePreview === "chamas" ? "active" : ""}
                                        onClick={() => setSidePreview("chamas")}
                                    >
                                        Chama
                                    </button>
                                    <button
                                        type="button"
                                        className={sidePreview === "fees" ? "active" : ""}
                                        onClick={() => setSidePreview("fees")}
                                    >
                                        Fees
                                    </button>
                                </div>
                            </div>
                            {sidePreview === "bills" ? (
                                <>
                                    <div className="subscription-preview-list">
                                        {subscriptionPreview.map((subscription) => (
                                            <div className="subscription-preview-row" key={subscription.id}>
                                                <SubscriptionIcon subscription={subscription} />
                                                <div>
                                                    <strong>{subscription.name}</strong>
                                                    <small>{dateFormatter.format(new Date(subscription.dueDate))}</small>
                                                </div>
                                                <span>{currencyFormatter.format(subscription.amount)}</span>
                                            </div>
                                        ))}
                                    </div>
                                    <button type="button" className="preview-link-button" onClick={() => navigate("/bills")}>
                                        View all bills
                                    </button>
                                </>
                            ) : sidePreview === "debts" ? (
                                <>
                                    <div className="debt-preview-list">
                                        {debtPreview.map((debt) => {
                                            const progress = getDebtProgress(debt);
                                            return (
                                                <div className="debt-preview-row" key={debt.id}>
                                                    <div>
                                                        <strong>{debt.name}</strong>
                                                        <small>{debt.type} · {debt.direction === "i_owe" ? "I owe" : "Owed to me"}</small>
                                                    </div>
                                                    <span>{currencyFormatter.format(debt.balance)}</span>
                                                    <DebtPulseLine progress={progress} />
                                                </div>
                                            )
                                        })}
                                    </div>
                                    <button type="button" className="preview-link-button" onClick={() => navigate("/debts")}>
                                        View all debts
                                    </button>
                                </>
                            ) : sidePreview === "chamas" ? (
                                <>
                                    <div className="chama-dashboard-preview">
                                        <div className="chama-dashboard-icon" aria-hidden="true">
                                            <HandCoins size={22} />
                                        </div>
                                        <div>
                                            <strong>{chamaPreview.name}</strong>
                                            <small>{chamaPreview.paidCount} of {chamaPreview.memberCount} paid · recipient {chamaPreview.currentRecipient}</small>
                                        </div>
                                    </div>
                                    <div className="budget-progress-track chama-dashboard-track" aria-hidden="true">
                                        <span style={{ width: `${getChamaProgress(chamaPreview)}%` }} />
                                    </div>
                                    <div className="chama-dashboard-meta">
                                        <span>{currencyFormatter.format(chamaPreview.poolAmount)} collected</span>
                                        <span>{getChamaProgress(chamaPreview)}%</span>
                                    </div>
                                    <button type="button" className="preview-link-button" onClick={() => navigate("/chamas")}>
                                        View chama tracker
                                    </button>
                                </>
                            ) : (
                                <>
                                    <div className="fees-dashboard-preview">
                                        <div className="fees-dashboard-icon" aria-hidden="true">
                                            <BadgePercent size={22} />
                                        </div>
                                        <div>
                                            <strong>{currencyFormatter.format(feeSummary.totalMonth)}</strong>
                                            <small>This month · highest: {feeSummary.highestProvider.name}</small>
                                        </div>
                                    </div>
                                    <div className="fees-dashboard-bars" aria-hidden="true">
                                        {feeSummary.providerTotals.slice(0, 4).map((provider) => (
                                            <span
                                                key={provider.id}
                                                style={{
                                                    height: `${Math.max(18, Math.round((provider.total / Math.max(feeSummary.highestProvider.total, 1)) * 72))}px`,
                                                    backgroundColor: provider.tone,
                                                }}
                                            />
                                        ))}
                                    </div>
                                    <div className="chama-dashboard-meta">
                                        <span>{currencyFormatter.format(feeSummary.totalWeek)} this week</span>
                                        <span>Mock</span>
                                    </div>
                                    <button type="button" className="preview-link-button" onClick={() => navigate("/fees")}>
                                        View fee tracker
                                    </button>
                                </>
                            )}
                        </section>
                    </aside>
                </div>
            </div>
        </div>

    );
}

export default Dashboard;

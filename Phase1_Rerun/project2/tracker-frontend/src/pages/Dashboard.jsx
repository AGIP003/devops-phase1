import { useEffect, useRef, useState } from "react";
import api from '../services/api'
import { getToken, removeToken } from "../utils/auth";
import { useNavigate, useOutletContext } from "react-router-dom";

import AddTransactionForm from "../components/auth/AddTransactionForm";
import { useMemo, useCallback } from "react";
import ChartsSection, { MonthlyTrendChart } from "../components/ui/ChartsSection";

import SummaryCards from "../components/ui/SummaryCard";

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

function Dashboard() {
    const navigate = useNavigate();
    const { toggleSidebar } = useOutletContext();
    const accountMenuRef = useRef(null);
    const addTransactionPanelRef = useRef(null);
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [showForm, setShowForm] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState("all");
    const [showAccountMenu, setShowAccountMenu] = useState(false);


    //Derived filtered list
    const filteredTransactions = useMemo(() => {
        return transactions.filter(transaction => {
            //Type filter
            if (filterType !== 'all' && transaction.type !== filterType) return false;
            //Search filter
            if (searchQuery) {
                const query = searchQuery.toLowerCase();
                const matchesDesc = transaction.description?.toLowerCase().includes(query);
                const matchesCat = transaction.category?.toLowerCase().includes(query);
                const matchesPM = transaction.payment_method?.toLowerCase().includes(query);
                if (!matchesCat && !matchesDesc && !matchesPM) return false;
            }

            return true;
        })
    }, [transactions, filterType, searchQuery]);

    //recent tables
    const recentTransactions = transactions.slice(0, 6);

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
            setTransactions(response.data);
            console.log('Transaction sample:', response.data[0]);
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    }, []);
    useEffect(() => {
        fetchTransactions();
    }, [])

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
    const currencyFormatter = new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES',
        maximumFractionDigits: 0,
    });

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
        }

        document.addEventListener("mousedown", handleClickOutside);

        return () => {
            document.removeEventListener("mousedown", handleClickOutside)
        };
    }, []);

    return (
        <div className="dashboard-page">
            <div className="dashboard-header">
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
                <div className="dashboard-header-actions">
                    <button
                        type="button"
                        onClick={() => setShowForm(prev => !prev)}
                        aria-expanded={showForm}
                        aria-controls="add-transaction-panel"
                    >
                        {showForm ? 'Cancel' : 'Add Transaction'}
                    </button>
                    <div className="account-menu-wrap" ref={accountMenuRef}>
                        <button
                            type="button"
                            className="profile-button"
                            aria-label="User profile menu"
                            aria-haspopup="menu"
                            aria-expanded={showAccountMenu}
                            onClick={() => setShowAccountMenu(prev => !prev)}
                        >
                            <span className="profile-initial">{username.charAt(0).toUpperCase()}</span>
                            <span>Profile</span>
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
            </div>
            <div className="dashboard-overview">
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
                                    <h2>Bills & Subscription</h2>
                                    <p>Upcoming recurring payments</p>
                                </div>
                            </div>
                            <div className="bills-placeholder">
                                No bills added yet
                            </div>
                        </section>
                    </aside>
                </div>
            </div>
        </div>

    );
}

export default Dashboard;

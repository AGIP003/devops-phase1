import { useEffect, useRef, useState } from "react";
import api from '../services/api'
import { getToken, removeToken } from "../utils/auth";
import { Navigate, useNavigate } from "react-router-dom";
import DeleteButton from "../components/auth/DeleteButton";
import AddTransactionForm from "../components/auth/AddTransactionForm";
import { useMemo } from "react";
import ChartsSection from "../components/auth/ChartsSection";
import { Eye,  EyeOff } from "lucide-react";

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
function Dashboard() {
    const navigate = useNavigate();
    const accountMenuRef = useRef(null);
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [showForm, setShowForm] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState("all");
    const [showAccountMenu, setShowAccountMenu] = useState(false);


    //Derived filtered list
    const filteredTransactions = transactions.filter(transaction => {
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
    });
    
    //recent tables
    const recentTransactions = transactions.slice(0, 6);

    //Date Formatter
    const dateFormatter = new Intl.DateTimeFormat('en-KE', {
        day:'2-digit',
        month: 'short',
        year: "numeric",
    });

    //summary cards
    const totalAmount = filteredTransactions.reduce((sum, t) => sum + Number(t.amount || 0), 0);
    const incomeTotal = filteredTransactions
        .filter(t => t.type === 'income')
        .reduce((sum, t) => sum + Number(t.amount || 0), 0);
    const expenseTotal = filteredTransactions
        .filter(t => t.type === 'expense')
        .reduce((sum, t) => sum + Number(t.amount || 0), 0);
    const currencyFormatter = new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES',
        maximumFractionDigits: 0,
    });

    //Fetch transactions
    async function fetchTransactions() {
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
    }
    useEffect(() => {
        fetchTransactions();
    }, [])

    function ChartSection({ transactions }) {
        if (transactions.length === 0 ) return null // to avoid rendering empty charts
    }

    //SkeltonRow
    function TransactionSkelton() {

        return (
            <tr>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', width: '80px' }} /></td>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', width: '60px' }} /></td>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', width: '120px' }} /></td>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', width: '70px' }} /></td>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', width: '70px' }} /></td>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', width: '70px' }} /></td>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', width: '70px' }} /></td>
            </tr>
        )
    }
    //useMemo catches the results and only computes when dependencies change
    //USED WHEN COMPUTING IS EXPENSIVE OR WANT GUARANTTEE IT ONLY RUNS ONCE
    const username = useMemo (() => getUsernameFromToken(), []);
   

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
                    <button type="button" className="icon-button" aria-label="Open sidebar">
                        ☰
                    </button>
                    <div>
                        <h1>Welcome, {username} </h1>
                        <p>Showing {filteredTransactions.length} of {transactions.length} transactions</p>
                    </div>
                </div>
                <div className="dashboard-header-actions">
                    <button onClick={() => setShowForm(prev => !prev)}>
                        {showForm ? 'Cancel' : 'Add Transaction'}
                    </button>
                    <div className="account-menu-wrap" ref={accountMenuRef}>
                        <button 
                            type="button" 
                            className="avatar-button" 
                            aria-label="Account menu"
                            onClick={() => setShowAccountMenu(prev => !prev)}
                        >
                            {username.charAt(0).toUpperCase()}
                        </button>

                        {showAccountMenu && (
                            <div className="account-menu">
                                <p>Signed in as</p>
                                <strong>{username}</strong>
                                <button type="button" onClick={() => {removeToken(); navigate('/');}}>
                                    Logout
                                </button>

                            </div>
                        )}
                    </div>
                </div>
            </div>
            <div className="dashboard-overview">
                <div className="summary-grid">
                    <div className="summary-card summary-card-total">
                        
                        <button 
                            type="button"
                            className="summary-privacy-toggle"
                            onClick={toggleHideAmounts}
                            aria-label={hideAmounts ? "Show amounts" : "Hide amounts"}
                        >
                            {hideAmounts ? <Eye size={16} /> : <EyeOff size ={16} />}       
                        </button>
                        <span>Total</span>
                        <strong>{hideAmounts ? "••••••" : currencyFormatter.format(totalAmount)}</strong>
                        <small>Current view</small>
                    </div>
                    <div className="summary-card summary-card-income">
                        <span>Income</span>
                        <strong>{hideAmounts ? "••••••" :currencyFormatter.format(incomeTotal)}</strong>
                        <small>{filteredTransactions.filter(t => t.type === 'income').length} transactions</small>
                    </div>
                    <div className="summary-card summary-card-expense">
                        <span>Expense</span>
                        <strong>{hideAmounts ? "••••••" :currencyFormatter.format(expenseTotal)}</strong>
                        <small>{filteredTransactions.filter(t => t.type === 'expense').length} transactions</small>
                    </div>
                    <div className = "summary-card summary-card-goal">
                        <span>Goal</span>
                        <strong>{hideAmounts ? "••••••" : "Not set"}</strong>
                        <small>Coming Soon</small>         
                    </div>
                </div>
                <div className="dashboard-charts-row">
                    <div className="chart-card chart-card-placeholder">
                        <h3>Monthly Trend</h3>
                        <p>Bar chart coming soon</p>
                    </div>
                    <ChartsSection
                        transactions={filteredTransactions}
                        filterType={filterType}                   
                    />
                </div>
            </div>
            
            <section className="recent-card">
                <div className="section-heading">
                    <div>
                        <h2>Recent Transactions</h2>
                    </div>

                    <button type="button">
                        View all
                    </button>
                </div>

                <div className="recent-table-head">
                    <span>S/N</span>
                    <span>Transaction</span>
                    <span>Amount</span>
                </div>

                <div className="recent-list">
                    {recentTransactions.map((tx, index) => (
                        <div className="recent-row" key={tx.id}>
                            <span className="recent-index">
                                {String(index + 1)}
                            </span>
                    
                            <div className="recent-main">
                                <strong>{tx.description}</strong>
                                <span>{tx.category} • {dateFormatter.format(new Date(tx.date))}</span>
                            </div>
                    
                            <span className={`recent-amount recent-amount-${tx.type}`}>
                                {tx.type === 'expense' ? '-' : '+'}
                                {currencyFormatter.format(Number(tx.amount || 0))}
                            </span>
                        </div>
                    ))}
                </div>
            </section>

            <div className="dashboard-toolbar">
                <input
                    type='text'
                    placeholder="Search..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
                <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                    <option value="all">All</option>
                    <option value="income">Income</option>
                    <option value="expense">Expense</option>
                </select>
            </div>
            {showForm && (
                <AddTransactionForm onSuccess={() => {
                    fetchTransactions();
                    setShowForm(false);
                }} />
            )}
            
        </div>

    );
}

export default Dashboard;

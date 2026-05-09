import { useEffect, useState } from "react";
import api from '../services/api'
import { getToken, removeToken } from "../utils/auth";
import { Navigate, useNavigate } from "react-router-dom";
import DeleteButton from "../components/auth/DeleteButton";
import AddTransactionForm from "../components/auth/AddTransactionForm";
import { useMemo } from "react";
import ChartsSection from "../components/auth/ChartsSection";

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
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [showForm, setShowForm] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState("all");

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
        setError(''); // reset the previous errors     nm 
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
    const navigate = useNavigate();
    return (
        <div className="dashboard-page">
            <div className="dashboard-header">
                <div>
                    <h1>Welcome, {username} </h1>
                    <p>Showing {filteredTransactions.length} of {transactions.length} transactions</p>
                </div>
            </div>

            <div className="summary-grid">
                <div className="summary-card summary-card-total">
                    <span>Total</span>
                    <strong>{currencyFormatter.format(totalAmount)}</strong>
                    <small>Current view</small>
                </div>
                <div className="summary-card summary-card-income">
                    <span>Income</span>
                    <strong>{currencyFormatter.format(incomeTotal)}</strong>
                    <small>{filteredTransactions.filter(t => t.type === 'income').length} transactions</small>
                </div>
                <div className="summary-card summary-card-expense">
                    <span>Expense</span>
                    <strong>{currencyFormatter.format(expenseTotal)}</strong>
                    <small>{filteredTransactions.filter(t => t.type === 'expense').length} transactions</small>
                </div>
            </div>
            
            <ChartsSection 
            transactions={filteredTransactions} 
            filterType={filterType}
            
            />

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

                <button onClick={() => setShowForm(prev => !prev)}>
                    {showForm ? 'Cancel' : 'Add Transaction'}
                </button>
                <button onClick={() => { removeToken(); navigate('/'); }}>Logout</button>
            </div>
            {showForm && (
                <AddTransactionForm onSuccess={() => {
                    fetchTransactions();
                    setShowForm(false);
                }} />
            )}


            {loading && <p>Loading...</p>}
            {error && (
                <p style={{ color: 'red' }}>
                    Error: {error} <button onClick={fetchTransactions}>Retry</button>
                </p>
            )}

            {!error && (
                <table border="1">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Description</th>
                            <th>Type</th>
                            <th>Category</th>
                            <th>Amount</th>
                            <th>Payment Method</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            [...Array(5)].map((_, i) => <TransactionSkelton key={i} />)
                            
                        ) : filteredTransactions.length === 0 ? (
                            <tr>
                                <td colSpan={7} style={{ textAlign: 'center' }}>
                                    {transactions.length === 0
                                        ? 'No transactions yet.'
                                        : 'No transactions match your search/filter'}
                                </td>
                            </tr>

                        ) : (filteredTransactions.map((tx) => (
                            <tr key={tx.id}>
                                <td>{tx.date}</td>
                                <td>{tx.description}</td>
                                <td>{tx.type}</td>
                                <td>{tx.category}</td>
                                <td>{tx.amount}</td>
                                <td>{tx.payment_method}</td>
                                <td>
                                    <DeleteButton
                                        transactionId={tx.id}
                                        onDeleted={fetchTransactions}
                                    />
                                </td>
                            </tr>
                        ))
                        )}
                    </tbody>
                </table>
            )}
            <div>

            </div>
        </div>

    );
}

export default Dashboard;

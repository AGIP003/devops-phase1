import { useEffect, useState } from "react";
import api from '../services/api'
import { getToken, removeToken } from "../utils/auth";
import { Navigate, useNavigate } from "react-router-dom";
import DeleteButton from "../components/auth/DeleteButton";
import AddTransactionForm from "../components/auth/AddTransactionForm";

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
            const matchesDesc = transactions.description?.toLowerCase().includes(query);
            const matchesCat = transactions.category?.toLowerCase().includes(query);
            const matchesPM = transactions.payment_method?.toLowerCase().includes(query);
            if (!matchesCat && !matchesDesc && !matchesPM) return false;
        }

        return true;
    });

    //summary cards
    const totalAmount = filteredTransactions.reduce((sum, t) => sum + t.amount, 0);
    const incomeTotal = filteredTransactions.filter(t => t.type === 'income').reduce((sum, t) => sum + t.amount, 0);
    const expenseTotal = filteredTransactions.filter(t => t.type === 'expense').reduce((sum, t) => sum + t.amount, 0);

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

    //SkeltonRow
    function TransactionSkelton() {
        return (
            <tr>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#1e293b', borderRadius: '4px', width: '80px' }} /></td>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', width: '60px' }} /></td>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#1e293b', borderRadius: '4px', width: '120px' }} /></td>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', width: '70px' }} /></td>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', width: '70px' }} /></td>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', width: '70px' }} /></td>
                <td style={{ textAlign: 'center' }}><div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', width: '70px' }} /></td>
            </tr>
        )
    }
    const username = getUsernameFromToken();
    const navigate = useNavigate();
    return (
        <div>
            <h1>Welcome, {username} </h1>

            <p> Showing {filteredTransactions.length} of {transactions.length} transactions</p>
            <div style={{ display: '', gap: '1rem' }}>
                <div>Total: KES {totalAmount}</div>
                <div>Income: KES{incomeTotal}</div>
                <div>Expense: KES{expenseTotal}</div>
            </div>

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
            {showForm && (
                <AddTransactionForm onSuccess={() => {
                    fetchTransactions();
                    setShowForm(false);
                }} />
            )}


            {loading && <p>Loading...</p>}
            {error && (
                <p style={{ color: 'red' }}>
                    Error: {error} <button onClick={() => window.location.reload()}>Retry</button>
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
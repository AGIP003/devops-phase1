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

    async function fetchTransactions() {
            setLoading(true);
            setError(''); // reset the previous errors     nm 
            try {
                const response = await api.get('/transactions');
                setTransactions(response.data);
            } catch (error) {
                setError(error.message);
            } finally {
                setLoading(false);
            }
        }
    useEffect(() => {
        fetchTransactions();
    }, [])

    const username = getUsernameFromToken();
    const navigate = useNavigate();
    return (
        <div>
            <h1>Welcome, {username} </h1>
           
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
                </p>)}
            {!loading && !error && transactions.length === 0 && <p>No transactions yet</p>}
            {!loading && !error && transactions.length > 0 && (
                <table border="1">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Description</th>
                            <th>Amount</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {transactions.map((tx) => (
                            <tr key={tx.id}>
                                <td>{tx.date}</td>
                                <td>{tx.description}</td>
                                <td>{tx.amount}</td>
                                <td>
                                    <DeleteButton 
                                        transactionId={tx.id} 
                                        onDeleted={fetchTransactions} 
                                    />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
            <div>
                
            </div>
        </div>

    );
}

export default Dashboard;
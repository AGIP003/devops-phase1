import { useEffect, useState } from "react";
import api from '../services/api'
import { getToken, removeToken } from "../utils/auth";
import { Navigate, useNavigate } from "react-router-dom";

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

    useEffect(() => {
        //Define async function inside
        async function fetchTransaction() {
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
        fetchTransaction()
    }, [])

    const username = getUsernameFromToken();
    const navigate = useNavigate();
    return (
        <div>
            <h1>Welcome, {username} </h1>
            <button onClick={() => { removeToken(); navigate('/'); }}>Logout</button>

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
                        </tr>
                    </thead>
                    <tbody>
                        {transactions.map((tx) => (
                            <tr key={tx.id}>
                                <td>{tx.date}</td>
                                <td>{tx.description}</td>
                                <td>{tx.amount}</td>
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
import { useState } from 'react';
import { toast } from 'react-hot-toast';
import api from '../../services/api';

export default function DeleteButton({ transactionId, onDeleted }) {
    const [loading, setLoading] = useState(false);

    async function handleDelete() {
        if (!window.confirm('Are you sure you want to delete this transaction?')) {
            return;
        }
        setLoading(true);
        try {
            await api.delete(`/transactions/${transactionId}`);
            onDeleted(); //tells Dashboard to refresh transactions
        } catch (err) {
            toast.error(err.response?.data?.message || err.message || 'Delete failed');
        } finally {
            setLoading(false);
        }
    }


    return (
        <button onClick={handleDelete} disabled={loading}>
            {loading ? '...' : 'Delete'}
        </button>
    );
}

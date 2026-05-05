import { useState } from 'react';
import api from '../../services/api';

function DeleteButton({ transactionId, onDeleted }) {
    const [loading, setLoading] = useState(false);

    async function handleDelete(){
        if(!window.confirm('Are you sure you want to delete this transaction?')){
            return;
        }
        setLoading(true);
        try {
            await api.delete(`/transactions/${transactionId}`);
            onDeleted(); //tells Dashboard to refresh transactions
        } catch (err) {
             alert(err.message || 'Delete failed');           
        }finally {
            setLoading(false);
        }
    }


    return(
        <button onClick={handleDelete} disabled={loading}>
            {loading ? '...' : 'Delete'}
        </button>
    );
}

export default DeleteButton;


import { useCallback, useEffect, useRef,  useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import api from '../services/api';
import { Navigate,useNavigate } from "react-router-dom";


function Transaction  () {
    const navigate = useNavigate();
    const [transactions, setTransactions] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState("all");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const dateFormatter = new Intl.DateTimeFormat('en-KE', {
        year: "numeric",
        day:'2-digit',
        month: 'short',
        
    });
    const [filterDate, setFilterDate] = useState('');

    //Derived filtered list
    const filteredTransactions = transactions.filter(transaction => {
        //Type filter
        if (filterType !== 'all' && transaction.type !== filterType) return false;
        //date filter
        if (filterDate) {
            const transactionDate = new Date(transaction.date).toISOString().slice(0, 10);
         if (transactionDate !== filterDate) return false;
}
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

    //Delete optimistic
    const handleDeleteOptimistic = async (id) => {
        // Assigning current state for rollback
        const previousTransactions = transactions
        //optimistic update to remove the transaction from UI immediately
        setTransactions(prev => prev.filter(t => t.id !== id));

        try {
            await api.delete(`/transactions/${id}`);
        } catch (err) {
            //rollback on error
            setTransactions(previousTransactions);
            alert(err.message || 'Delete failed');
        }
    };
   
    return (
        <div className="transactions-page">
            <div className="transactions-page-header">
                <div>
                    <h1 className="transactions-header">Transactions</h1>
                    <p>Search, filter and manage records</p>
                </div>
                
            </div>
            <div className="transactions-toolbar">
                <input
                    type='text'
                    placeholder="Search..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
                <div className="transactions-filter-group">
                    <input
                        type="date"
                        value={filterDate}
                        onChange={(e) => setFilterDate(e.target.value)}
                    />
                <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                    <option value="all">All</option>
                    <option value="income">Income</option>
                    <option value="expense">Expense</option>
                </select>
                </div>
            </div>

            <div className="transactions-table-card">
                {loading && <p>Loading...</p>}
                       {error && (
                           <p style={{ color: 'red' }}>
                               Error: {error} <button onClick={fetchTransactions}>Retry</button>
                           </p>
                       )}

                       {!error && (
                           <table className="transactions-table">
                               <thead>
                                   <tr>
                                       <th>Description</th>
                                       <th>Type</th>
                                       <th>Category</th>
                                       <th>Date</th>
                                       <th>Payment</th>
                                       <th className="amount-cell">Amount</th>
                                       <th className="actions-cell">Actions</th>
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
                                           <td className="transaction-description">{tx.description}</td>
                                           <td>
                                               <span className={`type-pill type-pill-${tx.type}`}>
                                                   {tx.type}
                                               </span>
                                           </td>
                                           <td>{tx.category}</td>
                                           <td>{dateFormatter.format(new Date(tx.date))}</td>
                                           <td>{tx.payment_method}</td>
                                           <td className={`amount-cell amount-${tx.type}`}>
                                               {tx.type === 'expense' ? '-' : '+'}
                                               {Number(tx.amount || 0).toLocaleString('en-KE')}
                                           </td>
                                           <td className="actions-cell">
                                               <button
                                                    onClick={() => navigate(`/transactions/edit/${tx.id}`)}
                                                    className="btn-edit"
                                                >
                                                    <Pencil size={16}></Pencil>
                                                </button>
                                                <button  
                                                    className="btn-delete"
                                                    onClick={() => handleDeleteOptimistic(tx.id)}
                                                >
                                                    <Trash2 size={16}></Trash2>
                                                </button>
                                           </td>
                                       </tr>
                                   ))
                                   )}
                               </tbody>
                           </table>
                       )}
                </div>
        </div>
            )       
       }

export default Transaction;

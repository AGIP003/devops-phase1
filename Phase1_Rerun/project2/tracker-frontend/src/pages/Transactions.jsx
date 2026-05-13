import DeleteButton from "../components/auth/DeleteButton";
import { useCallback, useEffect, useRef, useState } from "react";
import api from '../services/api';


function Transaction  () {
    const [transactions, setTransactions] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState("all");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const dateFormatter = new Intl.DateTimeFormat('en-KE', {
        day:'2-digit',
        month: 'short',
        year: "numeric",
    });
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
    return (
        <div>
            <div>
                <h1 className="transactions-header">Transactions</h1>
                <input
                    type='text'
                    placeholder="Search..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            <div className="transactions-table">
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
                                           <td>{dateFormatter.format(new Date(tx.date))}</td>
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
                </div>
        </div>
            )       
       }

export default Transaction;
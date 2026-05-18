
import { useEffect, useState } from "react";
import { Pencil, Trash2, X } from "lucide-react";
import { useForm } from 'react-hook-form';
import api from '../services/api';
import { useOutletContext } from "react-router-dom";


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

function TransactionEditDrawer({ transactionId, onClose, onSaved }) {
    const [serverError, setServerError] = useState('');
    const [loadingTransaction, setLoadingTransaction] = useState(true);
    const {
        register,
        handleSubmit,
        watch,
        reset,
        formState: { errors, isSubmitting, isDirty }
    } = useForm();

    const categoryOptions = {
        income: ["salary", "business", "freelance", "loan", "investments", "gifts", "debts paid", "other income"],
        expense: ["rent", "utilities", "food", "transport", "groceries", "loan", "airtime", "medical", "subscriptions", "entertainment", "education", "vacations", "tools/software", "personal care", "taxes", "black tax", "other expense"]
    };
    const paymentMethods = ["cash", "m-pesa", "airtel money", "t-kash", "equitel", "bank transfer", "debit card", "credit card", "paypal"];
    const selectedType = watch("type");
    const currentCategories = selectedType ? categoryOptions[selectedType] : [];

    useEffect(() => {
        async function fetchTransaction() {
            setLoadingTransaction(true);
            setServerError('');
            try {
                const response = await api.get(`/transactions/${transactionId}`);
                const data = response.data;

                if (data.date) {
                    const parsedDate = new Date(data.date);
                    if (!isNaN(parsedDate)) {
                        data.date = parsedDate.toISOString().split('T')[0];
                    }
                }

                reset(data);
            } catch (err) {
                setServerError(err.response?.data?.message || 'Failed to load transaction');
            } finally {
                setLoadingTransaction(false);
            }
        }

        fetchTransaction();
    }, [transactionId, reset]);

    async function onSubmit(data) {
        setServerError('');
        try {
            await api.put(`/transactions/${transactionId}`, data);
            onSaved();
        } catch (err) {
            setServerError(err.response?.data?.message || 'Update failed');
        }
    }

    return (
        <div className="drawer-backdrop" role="presentation" onClick={onClose}>
            <aside
                className="transaction-drawer"
                role="dialog"
                aria-modal="true"
                aria-labelledby="transaction-edit-title"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="drawer-header">
                    <div>
                        <h2 id="transaction-edit-title">Edit transaction</h2>
                        <p>Update the details without leaving the table.</p>
                    </div>
                    <button type="button" className="drawer-close" onClick={onClose} aria-label="Close edit drawer">
                        <X size={19} />
                    </button>
                </div>

                {serverError && <div className="transaction-form-message transaction-form-error">{serverError}</div>}

                {loadingTransaction ? (
                    <div className="drawer-loading">Loading transaction...</div>
                ) : (
                    <form className="drawer-form" onSubmit={handleSubmit(onSubmit)}>
                        <label className="transaction-field transaction-field-wide">
                            <span>Description</span>
                            <input
                                type="text"
                                {...register("description", {
                                    required: "Description is required",
                                    minLength: { value: 3, message: "At least 3 characters" }
                                })}
                            />
                            {errors.description && <span className="error">{errors.description.message}</span>}
                        </label>

                        <label className="transaction-field">
                            <span>Type</span>
                            <select {...register("type", { required: "Type is required" })}>
                                <option value="expense">Expense</option>
                                <option value="income">Income</option>
                            </select>
                            {errors.type && <span className="error">{errors.type.message}</span>}
                        </label>

                        <label className="transaction-field">
                            <span>Category</span>
                            <select {...register("category", { required: "Category is required" })} disabled={!selectedType}>
                                <option value="">Select category</option>
                                {currentCategories.map(cat => (
                                    <option key={cat} value={cat}>{cat}</option>
                                ))}
                            </select>
                            {errors.category && <span className="error">{errors.category.message}</span>}
                        </label>

                        <label className="transaction-field">
                            <span>Date</span>
                            <input
                                type="date"
                                {...register("date", { required: "Date is required" })}
                            />
                            {errors.date && <span className="error">{errors.date.message}</span>}
                        </label>

                        <label className="transaction-field">
                            <span>Payment method</span>
                            <select {...register("payment_method")}>
                                <option value="">Select payment method</option>
                                {paymentMethods.map(pm => (
                                    <option key={pm} value={pm}>{pm}</option>
                                ))}
                            </select>
                        </label>

                        <label className="transaction-field">
                            <span>Amount</span>
                            <input
                                type="number"
                                step="0.01"
                                {...register("amount", {
                                    required: "Amount is required",
                                    valueAsNumber: true,
                                    min: { value: 0.01, message: "Amount must be greater than 0" }
                                })}
                            />
                            {errors.amount && <span className="error">{errors.amount.message}</span>}
                        </label>

                        <div className="drawer-actions">
                            <button type="button" className="drawer-secondary-button" onClick={onClose}>
                                Cancel
                            </button>
                            <button className="drawer-primary-button" type="submit" disabled={isSubmitting || !isDirty}>
                                {isSubmitting ? 'Saving...' : 'Save changes'}
                            </button>
                        </div>
                    </form>
                )}
            </aside>
        </div>
    );
}
    
function Transaction  () {
    const { toggleSidebar } = useOutletContext();
    const [transactions, setTransactions] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState("all");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [editingTransactionId, setEditingTransactionId] = useState(null);
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
                <div className="dashboard-header-left">
                    <button type="button" className="icon-button" aria-label="Toggle sidebar" onClick={toggleSidebar}>
                        <span className="menu-icon" aria-hidden="true">
                            <span />
                            <span />
                            <span />
                        </span>
                    </button>
                    <div>
                        <h1 className="transactions-header">Transactions</h1>
                        <p>Search, filter and manage records</p>
                    </div>
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
                                               <div className="transaction-actions">
                                               <button
                                                    type="button"
                                                    onClick={() => setEditingTransactionId(tx.id)}
                                                    className="table-action-button table-action-edit"
                                                    aria-label={`Edit ${tx.description || 'transaction'}`}
                                                    title="Edit transaction"
                                                >
                                                    <Pencil size={17} strokeWidth={2.2}></Pencil>
                                                </button>
                                                <button  
                                                    type="button"
                                                    className="table-action-button table-action-delete"
                                                    onClick={() => handleDeleteOptimistic(tx.id)}
                                                    aria-label={`Delete ${tx.description || 'transaction'}`}
                                                    title="Delete transaction"
                                                >
                                                    <Trash2 size={17} strokeWidth={2.2}></Trash2>
                                                </button>
                                               </div>
                                           </td>
                                       </tr>
                                   ))
                                   )}
                               </tbody>
                           </table>
                       )}
                </div>
                {editingTransactionId && (
                    <TransactionEditDrawer
                        transactionId={editingTransactionId}
                        onClose={() => setEditingTransactionId(null)}
                        onSaved={() => {
                            setEditingTransactionId(null);
                            fetchTransactions();
                        }}
                    />
                )}
        </div>
            )       
       }

export default Transaction;

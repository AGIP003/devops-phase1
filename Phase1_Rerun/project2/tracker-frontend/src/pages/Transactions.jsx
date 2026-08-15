
import { useCallback, useEffect, useMemo, useState } from "react";
import { Calendar, ChevronDown, FileText, Pencil, Trash2, X } from "lucide-react";
import { useForm } from 'react-hook-form';
import api from '../services/api';
import { useOutletContext } from "react-router-dom";
import toast from "react-hot-toast";
import EmptyState from '../components/ui/EmptyState';
import { useAdjustedCurrency } from "../hooks/useAdjustedCurrency";


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

function getDateValue(dateValue) {
    if (!dateValue) return null;
    const parsedDate = new Date(dateValue);
    if (Number.isNaN(parsedDate.getTime())) return null;
    parsedDate.setHours(0, 0, 0, 0);
    return parsedDate;
}

function FilterSelect({ children, ...props }) {
    return (
        <span className="filter-select-wrap">
            <select {...props}>
                {children}
            </select>
            <ChevronDown size={17} aria-hidden="true" />
        </span>
    );
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
    const selectedDate = watch("date");
    const currentCategories = selectedType ? categoryOptions[selectedType] : [];

    useEffect(() => {
        async function fetchTransaction() {
            setLoadingTransaction(true);
            setServerError('');
            try {
                const response = await api.get(`/transactions/${transactionId}`);
                const data = response.data;
                if (!data || typeof data !== "object") {
                    throw new Error("The server returned an invalid transaction response");
                }

                if (data.date) {
                    const parsedDate = new Date(data.date);
                    if (!isNaN(parsedDate)) {
                        data.date = parsedDate.toISOString().split('T')[0];
                    }
                }

                reset(data);
            } catch (err) {
                setServerError(err.message || 'Failed to load transaction');
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
                        <X size={19} aria-hidden="true" />
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
                            <div className={`date-input-wrap ${!selectedDate ? "date-input-empty" : ""}`}>
                                <Calendar size={16} aria-hidden="true" />
                                {!selectedDate && <span className="date-placeholder">Select date</span>}
                                <input
                                    type="date"
                                    aria-label="Transaction date"
                                    {...register("date", { required: "Date is required" })}
                                />
                            </div>
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

function Transaction() {
    const { toggleSidebar } = useOutletContext();
    const { formatCurrency } = useAdjustedCurrency();
    const [transactions, setTransactions] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState("all");
    const [filterCategory, setFilterCategory] = useState("all");
    const [dateRange, setDateRange] = useState("all");
    const [customStartDate, setCustomStartDate] = useState("");
    const [customEndDate, setCustomEndDate] = useState("");
    const [sortOrder, setSortOrder] = useState("newest");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [editingTransactionId, setEditingTransactionId] = useState(null);
    const dateFormatter = new Intl.DateTimeFormat('en-KE', {
        year: "numeric",
        day: '2-digit',
        month: 'short',

    });
    const getDateRangeBounds = useCallback((rangeKey) => {
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        if (rangeKey === "today") {
            return { start: today, end: today };
        }

        if (rangeKey === "this-week") {
            const start = new Date(today);
            start.setDate(today.getDate() - today.getDay());
            return { start, end: today };
        }

        if (rangeKey === "this-month") {
            return {
                start: new Date(today.getFullYear(), today.getMonth(), 1),
                end: today,
            };
        }

        if (rangeKey === "last-month") {
            const start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            const end = new Date(today.getFullYear(), today.getMonth(), 0);
            return { start, end };
        }

        if (rangeKey === "custom" && (customStartDate || customEndDate)) {
            return {
                start: customStartDate ? getDateValue(customStartDate) : null,
                end: customEndDate ? getDateValue(customEndDate) : null,
            };
        }

        return { start: null, end: null };
    }, [customStartDate, customEndDate]);

    const categoryOptions = useMemo(() => {
        const categories = new Set();
        transactions.forEach((transaction) => {
            if (transaction.category) {
                categories.add(transaction.category);
            }
        });
        return Array.from(categories).sort((a, b) => a.localeCompare(b));
    }, [transactions]);

    const hasActiveFilters = Boolean(
        searchQuery ||
        filterType !== "all" ||
        filterCategory !== "all" ||
        dateRange !== "all" ||
        customStartDate ||
        customEndDate ||
        sortOrder !== "newest"
    );

    function resetFilters() {
        setSearchQuery("");
        setFilterType("all");
        setFilterCategory("all");
        setDateRange("all");
        setCustomStartDate("");
        setCustomEndDate("");
        setSortOrder("newest");
    }

    const filteredTransactions = useMemo(() => {
        const { start, end } = getDateRangeBounds(dateRange);
        const query = searchQuery.trim().toLowerCase();

        return (transactions || [])
            .filter(transaction => {
                if (filterType !== 'all' && transaction.type !== filterType) return false;
                if (filterCategory !== "all" && transaction.category !== filterCategory) return false;

                const transactionDate = getDateValue(transaction.date);
                if (start && (!transactionDate || transactionDate < start)) return false;
                if (end && (!transactionDate || transactionDate > end)) return false;

                if (query) {
                    const matchesDesc = transaction.description?.toLowerCase().includes(query);
                    const matchesCat = transaction.category?.toLowerCase().includes(query);
                    const matchesPM = transaction.payment_method?.toLowerCase().includes(query);
                    if (!matchesCat && !matchesDesc && !matchesPM) return false;
                }

                return true;
            })
            .sort((a, b) => {
                const aDate = getDateValue(a.date)?.getTime() || 0;
                const bDate = getDateValue(b.date)?.getTime() || 0;
                const aAmount = Number(a.amount || 0);
                const bAmount = Number(b.amount || 0);

                if (sortOrder === "oldest") return aDate - bDate;
                if (sortOrder === "highest") return bAmount - aAmount;
                if (sortOrder === "lowest") return aAmount - bAmount;
                return bDate - aDate;
            });
    }, [transactions, filterType, filterCategory, dateRange, searchQuery, sortOrder, getDateRangeBounds]);



    //Fetch transactions
    async function fetchTransactions() {
        setLoading(true);
        setError(''); // reset the previous errors     
        try {
            const response = await api.get('/transactions');
            const data = Array.isArray(response.data) ? response.data : [];
            setTransactions(data);
        } catch (error) {
            setError(error.message);
            setTransactions([]);
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
        toast.success("Transaction deleted");

        try {
            await api.delete(`/transactions/${id}`);
        } catch (err) {
            //rollback on error
            setTransactions(previousTransactions);
            toast.error(err.message || 'Delete failed');
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
                <div className="transactions-header-actions">
                    <button
                        type="button"
                        className="report-button"
                        onClick={() => toast.success("Report generation preview")}
                    >
                        <FileText size={17} aria-hidden="true" />
                        Generate Report
                    </button>
                </div>

            </div>
            <div className="transactions-toolbar">
                <input
                    type='text'
                    placeholder="Search description, category, payment"
                    aria-label="Search transactions"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
                <div className="transactions-filter-group">
                    <FilterSelect
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        aria-label="Filter transactions by type"
                    >
                        <option value="all">All</option>
                        <option value="income">Income</option>
                        <option value="expense">Expense</option>
                    </FilterSelect>
                    <FilterSelect
                        value={filterCategory}
                        onChange={(e) => setFilterCategory(e.target.value)}
                        aria-label="Filter transactions by category"
                    >
                        <option value="all">All categories</option>
                        {categoryOptions.map((category) => (
                            <option key={category} value={category}>{category}</option>
                        ))}
                    </FilterSelect>
                    <FilterSelect
                        value={dateRange}
                        onChange={(e) => setDateRange(e.target.value)}
                        aria-label="Filter transactions by date range"
                    >
                        <option value="all">Any date</option>
                        <option value="today">Today</option>
                        <option value="this-week">This week</option>
                        <option value="this-month">This month</option>
                        <option value="last-month">Last month</option>
                        <option value="custom">Custom</option>
                    </FilterSelect>
                    <FilterSelect
                        value={sortOrder}
                        onChange={(e) => setSortOrder(e.target.value)}
                        aria-label="Sort transactions"
                    >
                        <option value="newest">Newest first</option>
                        <option value="oldest">Oldest first</option>
                        <option value="highest">Highest amount</option>
                        <option value="lowest">Lowest amount</option>
                    </FilterSelect>
                    <button
                        type="button"
                        className="filter-reset-button"
                        onClick={resetFilters}
                        disabled={!hasActiveFilters}
                    >
                        Reset
                    </button>
                </div>
                {dateRange === "custom" && (
                    <div className="transactions-custom-dates">
                        <div className={`date-input-wrap date-input-wrap-filter ${!customStartDate ? "date-input-empty" : ""}`}>
                            <Calendar size={16} aria-hidden="true" />
                            {!customStartDate && <span className="date-placeholder">From</span>}
                            <input
                                type="date"
                                aria-label="Filter transactions from date"
                                value={customStartDate}
                                onChange={(e) => setCustomStartDate(e.target.value)}
                            />
                        </div>
                        <div className={`date-input-wrap date-input-wrap-filter ${!customEndDate ? "date-input-empty" : ""}`}>
                            <Calendar size={16} aria-hidden="true" />
                            {!customEndDate && <span className="date-placeholder">To</span>}
                            <input
                                type="date"
                                aria-label="Filter transactions to date"
                                value={customEndDate}
                                onChange={(e) => setCustomEndDate(e.target.value)}
                            />
                        </div>
                    </div>
                )}
            </div>

            <div className="transactions-table-card">
                {error && (
                    <p style={{ color: 'red' }}>
                        Error: {error} <button type="button" onClick={fetchTransactions} aria-label="Retry loading transactions">Retry</button>
                    </p>
                )}

                {!error && (
                    filteredTransactions.length === 0 && !loading ? (
                        <EmptyState
                            title="No transactions found"
                            message={hasActiveFilters ? "Try clearing or changing your filters" : "Add your first transaction to get started"}
                            actionLabel={hasActiveFilters ? null : "Add Transaction"}
                            actionPath="/transactions/add"
                        />
                    ) : (
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
                                ) : filteredTransactions.map((tx) => (
                                    <tr key={tx.id}>
                                        <td className="transaction-description" data-label="Description">{tx.description}</td>
                                        <td data-label="Type">
                                            <span className={`type-pill type-pill-${tx.type}`}>
                                                {tx.type}
                                            </span>
                                        </td>
                                        <td data-label="Category">{tx.category}</td>
                                        <td data-label="Date">{dateFormatter.format(new Date(tx.date))}</td>
                                        <td data-label="Payment">{tx.payment_method}</td>
                                        <td className={`amount-cell amount-${tx.type}`} data-label="Amount">
                                            {tx.type === 'expense' ? '-' : '+'}
                                            {formatCurrency(Number(tx.amount || 0))}
                                        </td>
                                        <td className="actions-cell" data-label="Actions">
                                            <div className="transaction-actions">
                                                <button
                                                    type="button"
                                                    onClick={() => setEditingTransactionId(tx.id)}
                                                    className="table-action-button table-action-edit"
                                                    aria-label={`Edit ${tx.description || 'transaction'}`}
                                                    title="Edit transaction"
                                                >
                                                    <Pencil size={17} strokeWidth={2.2} aria-hidden="true"></Pencil>
                                                </button>
                                                <button
                                                    type="button"
                                                    className="table-action-button table-action-delete"
                                                    onClick={() => handleDeleteOptimistic(tx.id)}
                                                    aria-label={`Delete ${tx.description || 'transaction'}`}
                                                    title="Delete transaction"
                                                >
                                                    <Trash2 size={17} strokeWidth={2.2} aria-hidden="true"></Trash2>
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ))}
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

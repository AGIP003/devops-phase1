import { useState } from "react";
import api from '../../services/api';



function AddTransactionForm({ onSuccess }) {
    const [formData, setFormData] = useState({
        amount: '',
        category: '',
        type: '',
        date: '',
        description: '',
        payment_method: ''
    });
    const [loading, setLoading] = useState(false);
    const[error, setError] = useState('');
    const [success, setSuccess] = useState('');

    function handleChange(e){
        const {name, value} = e.target;
        setFormData(prev=>({
            ...prev, //All existing fields
            [name]: value, //update only the field whose name matches
            //Reset category if the transaction type has been changed
            ...(name === 'type' && { category: '' })
        }));
    }

    function validateForm() {
        if(!formData.type) {
            return 'Please select a transaction type (Income or Expense)'
        }
        if (!formData.amount.trim() || !formData.category.trim() || !formData.payment_method.trim() || !formData.date.trim() || !formData.description.trim()) {
            return 'Kindly fill in the missing field';
        }

        return '';
    }

    async function handleSubmit(e) {
        //Prevent page reload
        e.preventDefault();

        const error = validateForm();
        if (error) {
            setError(error);
            return;
        }

        setLoading(true);
        setError('');
        setSuccess('');

        try {
            //API call
            const response = await api.post('/transactions', formData);
            onSuccess();
            setSuccess('Transaction added');
            console.log(response)
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    const categoryOptions = {
        income: ["salary", "business", "freelance", "loan", "investments", "gifts", "other income", "debts paid" ],
        expense: ["rent", "utilities", "food", "transport", "airtime", "groceries", "loan", "medical", "subscriptions", "entertainment", "education", "vacations", "tools/software", "personal care", "taxes", "black tax", "other expense"]
    }

    const currentCategories = formData.type ? categoryOptions[formData.type] : [];
    const categorySelectEnabled = formData.type !== '';

    const paymentMethodOptions = [
      "cash", "m-pesa", "airtel money", "t-kash", "equitel",
      "bank transfer", "debit card", "credit card", "paypal"
    ];
    return(
        <div className="add-transaction-panel">
            <h3>Add Transaction</h3>
            <form className="add-transaction-form" onSubmit={handleSubmit}>
                <label className="transaction-field">
                  <span>Date</span>
                  <input
                    type="date"
                    name="date"
                    value={formData.date}
                    onChange={handleChange}
                    disabled={loading}
                    required
                  />
                </label>
                <label className="transaction-field transaction-field-wide">
                  <span>Description</span>
                  <input
                    type="text"
                    name="description"
                    placeholder="e.g. Lunch, salary, fuel"
                    value={formData.description}
                    onChange={handleChange}
                    disabled={loading}
                    required
                  />
                </label>
                <label className="transaction-field">
                  <span>Type</span>
                  <select
                    name="type"
                    value={formData.type}
                    onChange={handleChange}
                    disabled={loading}
                    required
                  >
                    <option value="">Select type</option>
                    <option value="income">Income</option>
                    <option value="expense">Expense</option>
                  </select>
                </label>
                <label className="transaction-field">
                  <span>Category</span>
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleChange}
                    disabled={loading || !formData.type}
                    required
                  >

                  <option value="">{formData.type ? "Select category" : "Select income/expense type first"}</option>
                  {currentCategories.map((cat) => (
                    <option key={cat} value={cat.toLowerCase().replace(/ /g, '_')}>
                      {cat}
                    </option>
                  ))}
                  </select>
                </label>
                <label className="transaction-field">
                  <span>Amount</span>
                  <input
                    type="number"
                    name="amount"
                    placeholder="0"
                    value={formData.amount}
                    onChange={handleChange}
                    disabled={loading}
                    required
                  />
                </label>

                <label className="transaction-field">
                  <span>Payment method</span>
                  <select
                    name="payment_method"   // matches state key
                    value={formData.payment_method}
                    onChange={handleChange}
                    disabled={loading}
                    required
                  >
                    <option value="">Select payment method</option>
                    {paymentMethodOptions.map((method) => (
                      <option key={method} value={method}>
                        {method}
                      </option>
                    ))}
                  </select>
                </label>

                {error && <p className="transaction-form-message transaction-form-error">{error}</p>}
                {success && <p className="transaction-form-message transaction-form-success">{success}</p>}
                <button className="transaction-submit-button" type="submit" disabled={loading}>
                  {loading ? 'Adding...' : 'Add Transaction'}
                </button>
            </form>
        </div>
    );
}

export default AddTransactionForm;

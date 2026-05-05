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
        income: ["salary", "business", "freelance", "loan", "investments", "gifts", "loan", "other income" ],
        expense: ["rent", "utilities", "food", "transport", "airtime", "medical", "subscriptions", "entertainment", "education", "vacations", "tools/software", "personal_care", "taxes", "black tax", "other expense"]
    }

    const currentCategories = formData.type ? categoryOptions[formData.type] : [];
    const categorySelectEnabled = formData.type !== '';

    const paymentMethodOptions = [
      "cash", "m-pesa", "airtel money", "t-kash", "equitel",
      "bank transfer", "debit card", "credit card", "paypal"
    ];
    return(
        <div>
            <h3>Add Transaction</h3>
            <form onSubmit={handleSubmit}>
                <input
                  type="date"
                  name="date"
                  value={formData.date}
                  onChange={handleChange}
                  disabled={loading}
                  required
                />
                <input
                  type="text"
                  name="description"
                  placeholder="Description"
                  value={formData.description}
                  onChange={handleChange}
                  disabled={loading}
                  required
                />
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
                <input
                  type="number"
                  name="amount"
                  placeholder="Amount"
                  value={formData.amount}
                  onChange={handleChange}
                  disabled={loading}
                  required
                />

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

                {error && <p style={{ color: 'red' }}>{error}</p>}
                {success && <p style={{ color: 'green' }}>{success}</p>}
                <button type="submit" disabled={loading}>
                  {loading ? 'Adding...' : 'Add Transaction'}
                </button>
            </form>
        </div>
    );
}

export default AddTransactionForm;

import { useParams, useNavigate } from "react-router-dom";
import { useForm } from 'react-hook-form';
import { useEffect, useState } from "react";
import api from '../../services/api'

function EditTransaction() {
    const { id } = useParams()
    const navigate = useNavigate()
    const [serverError, setServerError] = useState(null)
    
    const {
        register,
        handleSubmit,
        watch,
        reset,
        formState: { errors, isSubmitting, isDirty}
    } = useForm()

    const categoryOptions = {
      income: ["salary", "business", "freelance", "loan", "investments", "gifts", "debts paid", "other income"],
      expense: ["rent", "utilities", "food", "transport", "groceries", "loan", "airtime", "medical", "subscriptions", "entertainment", "electricity", "education", "vacations", "tools/software", "personal care", "taxes", "black tax", "other expense"]
    };
    const paymentMethods = ["cash", "m-pesa", "airtel money", "t-kash", "equitel", "bank transfer", "debit card", "credit card", "paypal"];
    const selectedType = watch("type");
    const currentCategories = selectedType ? categoryOptions[selectedType] : [];
    //Fetch transactions and prefill the form
    useEffect (() => {
        async function fetchTransaction() {
            try {
                const response = await api.get(`/transactions/${id}`);
                //format the date into the right format
                const data = response.data;
                if (!data || typeof data !== "object") {
                    throw new Error("The server returned an invalid transaction response");
                }
                
                if (data.date) {
                    const parsedDate = new Date(data.date);
                    if (!isNaN(parsedDate)) {
                    data.date =parsedDate.toISOString().split('T')[0];
                    }
                }
                console.log('Fetched transaction:', data)
                reset(data); //sets all fields and resets the "Dirty" state - form knows the user has not changed anything
            
            }catch (err) {
                setServerError(err.message || 'Failed to load transaction');
            }
        }
        fetchTransaction();
    }, [id, reset]); // re-runs if id changes; reset is stable

    // submit handler (called by react hook form after validation)
    const onSubmit = async (data) => {
        try {
            await api.put(`/transactions/${id}`, data);
            navigate('/transactions');
        } catch (err) {
            setServerError(err.response?.data?.message || 'Update failed');
        }
    };


    return (
        <div className="edit-transaction">
            {serverError && <div className="error-banner">{serverError}</div>}

        
            <form onSubmit={handleSubmit(onSubmit)}>
                <div className="form-field">
                    <label htmlFor="edit-description">Description</label>
                    <input
                        id="edit-description"
                        type="text" 
                        {...register("description", {
                            required: "Description is required",
                            minLength: { value: 3, message: "At least 3 characters"}
                        })}
                    />
                    {errors.description && <span className="error">{errors.description.message}</span>}
                </div>
                        {/* Type (income/expense) */}
                        <div className="form-field">
                          <label htmlFor="edit-type">Type</label>
                          <select id="edit-type" {...register("type", { required: "Type is required" })}>
                            <option value="expense">Expense</option>
                            <option value="income">Income</option>
                          </select>
                          {errors.type && <span className="error">{errors.type.message}</span>}
                        </div>

                        {/* Category */}
                        <div className="form-field">
                          <label htmlFor="edit-category">Category</label>
                          <select id="edit-category" {...register("category", { required: "Category is required" })} disabled={!selectedType}>
                            <option value="">Select category</option>
                            {currentCategories.map(cat => (
                              <option key={cat} value={cat}>{cat}</option>
                            ))}
                          </select>
                          {errors.category && <span className="error">{errors.category.message}</span>}
                        </div>

                        {/* Date */}
                        <div className="form-field">
                          <label htmlFor="edit-date">Date</label>
                          <input
                            id="edit-date"
                            type="date"
                            {...register("date", { required: "Date is required" })}
                          />
                          {errors.date && <span className="error">{errors.date.message}</span>}
                        </div>

                        {/* Payment method */}
                        <div className="form-field">
                          <label htmlFor="edit-payment-method">Payment Method</label>
                          <select id="edit-payment-method" {...register("payment_method")}>
                            <option value="">Select payment method</option>
                            {paymentMethods.map(pm => (
                              <option key={pm} value={pm}>{pm}</option>
                            ))}
                          </select>
                        </div>

                        {/* Amount */}
                        <div className="form-field">
                          <label htmlFor="edit-amount">Amount</label>
                          <input 
                            id="edit-amount"
                            type="number"
                            step="0.01"
                            {...register("amount", {
                              required: "Amount is required",
                              valueAsNumber: true,
                              min: { value: 0.01, message: "Amount must be greater than 0"}
                            })}
                          />
                            {errors.amount && <span className="error">{errors.amount.message}</span>}
            
                        </div>

                        <div className="form-actions">
                          <button type="button" onClick={() => navigate(-1)}>
                            Cancel
                          </button>
                          <button
                            type="submit"
                            disabled={isSubmitting || !isDirty}
                          >
                            {isSubmitting ? 'Saving...' : 'Save Changes'}
                          </button>
                    </div>
                
            </form>
        </div>
    );
}

export default EditTransaction;

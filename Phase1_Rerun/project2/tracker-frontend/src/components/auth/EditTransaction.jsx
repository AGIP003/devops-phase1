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
      expense: ["rent", "utilities", "food", "transport", "groceries", "loan", "airtime", "medical", "subscriptions", "entertainment", "education", "vacations", "tools/software", "personal care", "taxes", "black tax", "other expense"]
    };
    const paymentMethods = ["cash", "m-pesa", "airtel money", "t-kash", "equitel", "bank transfer", "debit card", "credit card", "paypal"];
    const selectedType = watch("type");
    const currentCategories = selectedType ? categoryOptions[selectedType] : [];
    //Fetch transactions and prefill the form
    useEffect (() => {
        async function fetchTransaction() {
            try {
                const response = await api.get(`transactions/${id}`);
                //format the date into the right format
                const data = response.data;
                
                if (data.date) {
                    const parsedDate = new Date(data.date);
                    if (!isNaN(parsedDate)) {
                    data.date =parsedDate.toISOString().split('T')[0];
                    }
                }
                console.log('Fetched transaction:', data)
                reset(data); //sets all fields and resets the "Dirty" state - form knows the user has not changed anything
            
            }catch (err) {
                setServerError(err.response?.data?.message || 'Failed to load transactions');
            }
        }
        fetchTransaction();
    }, [id, reset]); // re-runs if id changes; reset is stable

    // submit handler (called by react hook form after validation)
    const onSubmit = async (data) => {
        try {
            await api.put(`/transactions/${id}`, data);
            navigate('/transactions');
            reset();
        } catch (err) {
            setServerError(err.response?.data?.message || 'Update failed');
        }
    };


    return (
        <div className="edit-transaction">
            {serverError && <div className="error-banner">{serverError}</div>}

        
            <form onSubmit={handleSubmit(onSubmit)}>
                <div className="form-field">
                    <label>Description</label>
                    <input type="text" 
                        {...register("description", {
                            required: "Description is required",
                            minLength: { value: 3, message: "At least 3 characters"}
                        })}
                    />
                    {errors.description && <span className="error">{errors.description.message}</span>}
                </div>
                        {/* Type (income/expense) */}
                        <div className="form-field">
                          <label>Type</label>
                          <select {...register("type", { required: "Type is required" })}>
                            <option value="expense">Expense</option>
                            <option value="income">Income</option>
                          </select>
                          {errors.type && <span className="error">{errors.type.message}</span>}
                        </div>

                        {/* Category */}
                        <div className="form-field">
                          <label>Category</label>
                          <select {...register("category", { required: "Category is required" })} disabled={!selectedType}>
                            <option value="">Select category</option>
                            {currentCategories.map(cat => (
                              <option key={cat} value={cat}>{cat}</option>
                            ))}
                          </select>
                          {errors.category && <span className="error">{errors.category.message}</span>}
                        </div>

                        {/* Date */}
                        <div className="form-field">
                          <label>Date</label>
                          <input
                            type="date"
                            {...register("date", { required: "Date is required" })}
                          />
                          {errors.date && <span className="error">{errors.date.message}</span>}
                        </div>

                        {/* Payment method */}
                        <div className="form-field">
                          <label>Payment Method</label>
                          <select {...register("payment_method")}>
                            <option value="">Select payment method</option>
                            {paymentMethods.map(pm => (
                              <option key={pm} value={pm}>{pm}</option>
                            ))}
                          </select>
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
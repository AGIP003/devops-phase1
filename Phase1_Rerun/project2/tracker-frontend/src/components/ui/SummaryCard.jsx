import React from "react";
import { Eye,  EyeOff } from "lucide-react";

const SummaryCards = React.memo(function SummaryCards({ filteredTransactions, toggleHideAmounts, hideAmounts, currencyFormatter }) {
    //summary cards
    const incomeTotal = filteredTransactions
        .filter(t => t.type === 'income')
        .reduce((sum, t) => sum + Number(t.amount || 0), 0);
    const expenseTotal = filteredTransactions
        .filter(t => t.type === 'expense')
        .reduce((sum, t) => sum + Number(t.amount || 0), 0);  
    const balanceTotal = incomeTotal - expenseTotal;
    
    return (
        <div className="summary-grid">
            <div className="summary-card summary-card-income">
                <span>Income</span>
                <strong>{hideAmounts ? "••••••" :currencyFormatter.format(incomeTotal)}</strong>
                <small>{filteredTransactions.filter(t => t.type === 'income').length} transactions</small>
            </div>
            <div className="summary-card summary-card-expense">
                <span>Expense</span>
                <strong>{hideAmounts ? "••••••" :currencyFormatter.format(expenseTotal)}</strong>
                <small>{filteredTransactions.filter(t => t.type === 'expense').length} transactions</small>
            </div>
            <div className="summary-card summary-card-balance">
                <button 
                    type="button"
                    className="summary-privacy-toggle"
                    onClick={toggleHideAmounts}
                    aria-label={hideAmounts ? "Show amounts" : "Hide amounts"}
                >
                    {hideAmounts ? <Eye size={16} aria-hidden="true" /> : <EyeOff size ={16} aria-hidden="true" />}       
                </button>
                <span>Balance</span>
                <strong>{hideAmounts ? "••••••" : currencyFormatter.format(balanceTotal)}</strong>
                <small>Income minus expenses</small>
            </div>
            <div className = "summary-card summary-card-goal">
                <span>Goal</span>
                <strong>{hideAmounts ? "••••••" : "Not set"}</strong>
                <small>Coming Soon</small>         
            </div>
        </div>
    )
})

export default SummaryCards;

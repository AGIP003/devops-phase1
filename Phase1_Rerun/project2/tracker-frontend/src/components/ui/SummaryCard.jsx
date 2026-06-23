import React from "react";
import { Eye, EyeOff, MoreVertical, Target, TrendingDown, Wallet, Scale } from "lucide-react";
import { debts, getDebtSummary, getGoalProgress, savingsGoals } from "../../data/mockFinanceFeatures";

function SummaryDebtPulseLine({ progress }) {
    return (
        <div className="summary-debt-pulse" style={{ "--debt-progress": `${progress}%` }} aria-hidden="true">
            <svg viewBox="0 0 240 34" preserveAspectRatio="none">
                <path d="M2 20 H42 L51 10 L62 27 L75 14 L88 20 H126 L136 7 L150 29 L166 15 L180 20 H238" />
            </svg>
            <span />
        </div>
    )
}

function SummaryGoalRing({ progress }) {
    return (
        <div className="summary-goal-ring" style={{ "--goal-progress": `${progress}%` }} aria-label={`${progress}% saved`}>
            <span />
        </div>
    )
}

const SummaryCards = React.memo(function SummaryCards({ filteredTransactions, toggleHideAmounts, hideAmounts, currencyFormatter }) {
    //summary cards
    const txList = filteredTransactions || [];
    const incomeTotal = txList
        .filter(t => t.type === 'income')
        .reduce((sum, t) => sum + Number(t.amount || 0), 0);
    const expenseTotal = txList
        .filter(t => t.type === 'expense')
        .reduce((sum, t) => sum + Number(t.amount || 0), 0);
    const balanceTotal = incomeTotal - expenseTotal;
    const topGoal = savingsGoals[0];
    const goalProgress = getGoalProgress(topGoal);
    const debtSummary = getDebtSummary(debts);
    const debtProgress = Math.min(100, Math.round((debtSummary.owedToYou / Math.max(debtSummary.youOwe, 1)) * 100));
    const [expenseMode, setExpenseMode] = React.useState("expenses");
    const showingDebt = expenseMode === "debt";

    React.useEffect(() => {
        const intervalId = window.setInterval(() => {
            setExpenseMode(prev => prev === "expenses" ? "debt" : "expenses");
        }, 120000);

        return () => window.clearInterval(intervalId);
    }, []);

    return (
        <div className="summary-grid">
            <div className="summary-card summary-card-income">
                <button
                    type="button"
                    className="summary-privacy-toggle"
                    onClick={toggleHideAmounts}
                    aria-label={hideAmounts ? "Show amounts" : "Hide amounts"}
                >
                    {hideAmounts ? <Eye size={16} aria-hidden="true" /> : <EyeOff size={16} aria-hidden="true" />}
                </button>
                <span className="summary-label-with-icon">
                    <Wallet size={15} aria-hidden="true" />
                    Income
                </span>
                <strong>{hideAmounts ? "••••••" : currencyFormatter.format(incomeTotal)}</strong>
                <small>{txList.filter(t => t.type === 'income').length} transactions</small>
            </div>
            <div className="summary-card summary-card-expense">
                <div className="summary-card-topline">
                    <span className="summary-label-with-icon">
                        {showingDebt ? <Scale size={15} aria-hidden="true" /> : <TrendingDown size={15} aria-hidden="true" />}
                        {showingDebt ? "Total Debt" : "Expense"}
                    </span>
                    <div className="summary-mini-toggle" aria-label="Switch expense card view">
                        <button
                            type="button"
                            className={!showingDebt ? "active" : ""}
                            onClick={() => setExpenseMode("expenses")}
                        >
                            Expenses
                        </button>
                        <button
                            type="button"
                            className={showingDebt ? "active" : ""}
                            onClick={() => setExpenseMode("debt")}
                        >
                            Debt
                        </button>
                    </div>
                </div>
                <strong>{hideAmounts ? "••••••" : currencyFormatter.format(showingDebt ? debtSummary.youOwe : expenseTotal)}</strong>
                {showingDebt && <SummaryDebtPulseLine progress={debtProgress} />}
                <small>{showingDebt ? `${debtProgress}% offset by receivables` : `${txList.filter(t => t.type === 'expense').length} transactions`}</small>
            </div>
            <div className="summary-card summary-card-balance">

                <span className="summary-label-with-icon">
                    <Scale size={15} aria-hidden="true" />
                    Balance
                </span>
                <strong>{hideAmounts ? "••••••" : currencyFormatter.format(balanceTotal)}</strong>
                <small>Current View</small>
            </div>
            <div className="summary-card summary-card-goal">
                <div className="summary-goal-header">
                    <span className="summary-goal-title">
                        <Target size={16} aria-hidden="true" />
                        Goal
                    </span>
                    <button type="button" aria-label="Goal options">
                        <MoreVertical size={16} aria-hidden="true" />
                    </button>
                </div>
                <div className="summary-goal-body">
                    <SummaryGoalRing progress={goalProgress} />
                    <div className="summary-goal-copy">
                        <strong>{topGoal.name}</strong>
                        <small>Required: {hideAmounts ? "••••••" : currencyFormatter.format(topGoal.targetAmount)}</small>
                        <small>Collect: {hideAmounts ? "••••••" : currencyFormatter.format(topGoal.savedAmount)}</small>
                    </div>
                </div>
            </div>
        </div>
    )
})

export default SummaryCards;

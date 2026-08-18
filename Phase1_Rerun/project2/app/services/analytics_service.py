"""Database-backed personal-finance analytics.

The service deliberately keeps actual cash flow separate from planned or
future commitments. Combining them would double-count bills once their payment
also appears as a transaction.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import case, func, select

from app.extensions import db
from app.models.budget import Budget, BudgetItem
from app.models.category import Category
from app.models.debt import Debt, DebtEntry, DebtSchedule
from app.models.recurring_commitment import RecurringCommitment
from app.models.savings_goal import SavingsGoal, SavingsGoalEntry
from app.models.transaction import Transaction


ZERO = Decimal("0")
MONEY = Decimal("0.01")
SUPPORTED_PERIODS = {"30-days", "90-days", "6-months", "12-months", "all"}


class AnalyticsPeriodError(ValueError):
    """Raised when an unsupported analytics period is requested."""


def _money(value: Decimal | int | None) -> str:
    return format(Decimal(value or ZERO).quantize(MONEY, rounding=ROUND_HALF_UP), "f")


def _percentage(numerator: Decimal, denominator: Decimal) -> str | None:
    if denominator <= ZERO:
        return None
    return format(
        ((numerator / denominator) * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ),
        "f",
    )


def _subtract_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 - months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    return date(year, month, min(value.day, monthrange(year, month)[1]))


def resolve_period(period: str, *, today: date | None = None) -> tuple[date | None, date]:
    """Return an inclusive date range for a supported period key."""
    if period not in SUPPORTED_PERIODS:
        raise AnalyticsPeriodError(
            f"Unsupported period '{period}'. Choose one of: "
            + ", ".join(sorted(SUPPORTED_PERIODS))
        )

    end = today or date.today()
    if period == "all":
        return None, end
    if period == "30-days":
        return end - timedelta(days=29), end
    if period == "90-days":
        return end - timedelta(days=89), end
    if period == "6-months":
        return _subtract_months(end, 6) + timedelta(days=1), end
    return _subtract_months(end, 12) + timedelta(days=1), end


def _dated(statement, column, start: date | None, end: date):
    statement = statement.where(column <= end)
    return statement.where(column >= start) if start is not None else statement


def _transaction_aggregates(user_id: int, start: date | None, end: date):
    base_filters = (
        Transaction.user_id == user_id,
        Transaction.deleted_at.is_(None),
    )

    totals_statement = (
        select(Category.type, func.coalesce(func.sum(Transaction.amount), ZERO))
        .select_from(Transaction)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(*base_filters)
        .group_by(Category.type)
    )
    totals_statement = _dated(totals_statement, Transaction.date, start, end)
    totals_by_type = {
        transaction_type: Decimal(total)
        for transaction_type, total in db.session.execute(totals_statement)
    }

    monthly_statement = (
        select(
            func.date_trunc("month", Transaction.date).label("month"),
            Category.type,
            func.coalesce(func.sum(Transaction.amount), ZERO),
        )
        .select_from(Transaction)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(*base_filters)
        .group_by("month", Category.type)
        .order_by("month")
    )
    monthly_statement = _dated(monthly_statement, Transaction.date, start, end)
    monthly: dict[str, dict[str, Decimal]] = {}
    for month, transaction_type, total in db.session.execute(monthly_statement):
        key = month.date().isoformat()[:7]
        values = monthly.setdefault(key, {"income": ZERO, "expense": ZERO})
        if transaction_type in values:
            values[transaction_type] = Decimal(total)

    category_statement = (
        select(
            func.coalesce(Category.name, "Uncategorized"),
            func.coalesce(func.sum(Transaction.amount), ZERO),
        )
        .select_from(Transaction)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(*base_filters, Category.type == "expense")
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )
    category_statement = _dated(category_statement, Transaction.date, start, end)
    categories = [
        {"category": name, "amount": _money(total)}
        for name, total in db.session.execute(category_statement)
    ]

    daily_statement = (
        select(
            Transaction.date,
            func.coalesce(
                func.sum(case((Category.type == "income", Transaction.amount), else_=ZERO)),
                ZERO,
            ),
            func.coalesce(
                func.sum(case((Category.type == "expense", Transaction.amount), else_=ZERO)),
                ZERO,
            ),
            func.count(Transaction.id),
        )
        .select_from(Transaction)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(*base_filters)
        .group_by(Transaction.date)
        .order_by(Transaction.date)
    )
    daily_statement = _dated(daily_statement, Transaction.date, start, end)
    daily = [
        {
            "date": occurred_on.isoformat(),
            "income": _money(income),
            "expenses": _money(expenses),
            "transactionCount": count,
        }
        for occurred_on, income, expenses, count in db.session.execute(daily_statement)
    ]

    return totals_by_type, monthly, categories, daily


def _monthly_equivalent(amount: Decimal, frequency: str, custom_days: int | None) -> Decimal:
    factors = {
        "weekly": Decimal("52") / Decimal("12"),
        "monthly": Decimal("1"),
        "quarterly": Decimal("1") / Decimal("3"),
        "termly": Decimal("3") / Decimal("12"),
        "yearly": Decimal("1") / Decimal("12"),
    }
    if frequency == "custom" and custom_days:
        return amount * (Decimal("365.2425") / Decimal(custom_days)) / Decimal("12")
    return amount * factors.get(frequency, Decimal("0"))


def _commitment_summary(user_id: int):
    statement = select(
        RecurringCommitment.kind,
        RecurringCommitment.amount,
        RecurringCommitment.frequency,
        RecurringCommitment.custom_interval_days,
        RecurringCommitment.currency_code,
    ).where(
        RecurringCommitment.user_id == user_id,
        RecurringCommitment.status == "active",
        RecurringCommitment.deleted_at.is_(None),
    )

    totals = {"bill": ZERO, "subscription": ZERO}
    unsupported_currencies: set[str] = set()
    for kind, amount, frequency, custom_days, currency in db.session.execute(statement):
        if currency != "KES":
            unsupported_currencies.add(currency)
            continue
        totals[kind] += _monthly_equivalent(Decimal(amount), frequency, custom_days)
    return totals, sorted(unsupported_currencies)


def _budget_summary(user_id: int):
    planned = db.session.scalar(
        select(func.coalesce(func.sum(Budget.target_amount), ZERO)).where(
            Budget.user_id == user_id
        )
    )
    actual = db.session.scalar(
        select(func.coalesce(func.sum(BudgetItem.actual_amount), ZERO))
        .select_from(BudgetItem)
        .join(Budget, BudgetItem.budget_id == Budget.id)
        .where(Budget.user_id == user_id)
    )
    planned_value, actual_value = Decimal(planned), Decimal(actual)
    return {
        "planned": _money(planned_value),
        "spent": _money(actual_value),
        "remaining": _money(planned_value - actual_value),
        "usedPercentage": _percentage(actual_value, planned_value),
    }


def _debt_summary(user_id: int, start: date | None, end: date):
    entry_delta = case(
        (DebtEntry.entry_type.in_(("interest", "fee", "adjustment_increase")), DebtEntry.amount),
        (DebtEntry.entry_type.in_(("repayment", "adjustment_decrease")), -DebtEntry.amount),
        else_=ZERO,
    )
    # Sum per-debt balances in Python to avoid multiplying opening balances by entries.
    balance_rows = db.session.execute(
        select(
            Debt.opening_balance,
            func.coalesce(func.sum(entry_delta), ZERO),
        )
        .select_from(Debt)
        .outerjoin(DebtEntry, DebtEntry.debt_id == Debt.id)
        .where(Debt.user_id == user_id, Debt.status == "active", Debt.deleted_at.is_(None))
        .group_by(Debt.id, Debt.opening_balance)
    )
    current_balance = sum(
        (max(Decimal(opening) + Decimal(delta), ZERO) for opening, delta in balance_rows),
        ZERO,
    )

    entry_statement = (
        select(
            DebtEntry.entry_type,
            func.coalesce(func.sum(DebtEntry.amount), ZERO),
        )
        .select_from(DebtEntry)
        .join(Debt, DebtEntry.debt_id == Debt.id)
        .where(Debt.user_id == user_id, Debt.deleted_at.is_(None))
        .group_by(DebtEntry.entry_type)
    )
    entry_statement = _dated(entry_statement, DebtEntry.occurred_on, start, end)
    entries = {kind: Decimal(total) for kind, total in db.session.execute(entry_statement)}

    schedule_rows = db.session.execute(
        select(
            DebtSchedule.installment_amount,
            DebtSchedule.frequency,
            DebtSchedule.interval_count,
        )
        .select_from(DebtSchedule)
        .join(Debt, DebtSchedule.debt_id == Debt.id)
        .where(
            Debt.user_id == user_id,
            Debt.status == "active",
            Debt.deleted_at.is_(None),
        )
    )
    scheduled = ZERO
    schedule_factors = {
        "daily": Decimal("365.2425") / Decimal("12"),
        "weekly": Decimal("52") / Decimal("12"),
        "monthly": Decimal("1"),
    }
    for amount, frequency, interval_count in schedule_rows:
        if amount is None or frequency == "one_time":
            continue
        scheduled += (
            Decimal(amount)
            * schedule_factors[frequency]
            / Decimal(interval_count)
        )
    return {
        "activeBalance": _money(current_balance),
        "periodRepayments": _money(entries.get("repayment", ZERO)),
        "periodFees": _money(entries.get("fee", ZERO)),
        "monthlyScheduledPayments": _money(scheduled),
    }


def _goal_summary(user_id: int, today: date):
    statement = (
        select(
            SavingsGoal.id,
            SavingsGoal.target_amount,
            SavingsGoal.target_date,
            SavingsGoal.currency_code,
            func.coalesce(
                func.sum(
                    case(
                        (SavingsGoalEntry.entry_type == "contribution", SavingsGoalEntry.amount),
                        else_=-SavingsGoalEntry.amount,
                    )
                ),
                ZERO,
            ),
        )
        .outerjoin(SavingsGoalEntry, SavingsGoalEntry.goal_id == SavingsGoal.id)
        .where(SavingsGoal.user_id == user_id, SavingsGoal.deleted_at.is_(None))
        .group_by(SavingsGoal.id)
    )

    target = current = required_monthly = ZERO
    unsupported_currencies: set[str] = set()
    count = 0
    for _, goal_target, target_date, currency, saved in db.session.execute(statement):
        if currency != "KES":
            unsupported_currencies.add(currency)
            continue
        count += 1
        goal_target, saved = Decimal(goal_target), max(Decimal(saved), ZERO)
        target += goal_target
        current += saved
        remaining = max(goal_target - saved, ZERO)
        months_left = max(
            Decimal("1"),
            Decimal(max((target_date - today).days, 0)) / Decimal("30.4375"),
        )
        required_monthly += remaining / months_left

    return {
        "activeCount": count,
        "target": _money(target),
        "saved": _money(current),
        "remaining": _money(max(target - current, ZERO)),
        "progressPercentage": _percentage(current, target),
        "requiredMonthlyContribution": _money(required_monthly),
    }, sorted(unsupported_currencies)


def _upcoming(user_id: int, today: date):
    commitment_rows = db.session.execute(
        select(
            RecurringCommitment.id,
            RecurringCommitment.kind,
            RecurringCommitment.name,
            RecurringCommitment.amount,
            RecurringCommitment.next_due_date,
        )
        .where(
            RecurringCommitment.user_id == user_id,
            RecurringCommitment.status == "active",
            RecurringCommitment.deleted_at.is_(None),
            RecurringCommitment.next_due_date >= today,
            RecurringCommitment.currency_code == "KES",
        )
        .order_by(RecurringCommitment.next_due_date)
        .limit(8)
    )
    debt_rows = db.session.execute(
        select(Debt.id, Debt.title, DebtSchedule.installment_amount, DebtSchedule.next_due_date)
        .join(DebtSchedule, DebtSchedule.debt_id == Debt.id)
        .where(
            Debt.user_id == user_id,
            Debt.status == "active",
            Debt.deleted_at.is_(None),
            DebtSchedule.next_due_date >= today,
            Debt.currency_code == "KES",
        )
        .order_by(DebtSchedule.next_due_date)
        .limit(8)
    )
    items = [
        {"id": identifier, "kind": kind, "name": name, "amount": _money(amount), "dueDate": due.isoformat()}
        for identifier, kind, name, amount, due in commitment_rows
    ]
    items.extend(
        {"id": identifier, "kind": "debt", "name": name, "amount": _money(amount), "dueDate": due.isoformat()}
        for identifier, name, amount, due in debt_rows
        if amount is not None
    )
    return sorted(items, key=lambda item: item["dueDate"])[:8]


def build_analytics_summary(user_id: int, period: str, *, today: date | None = None):
    """Build a user-owned analytics read model using database aggregates."""
    current_date = today or date.today()
    start, end = resolve_period(period, today=current_date)
    totals, monthly, categories, daily = _transaction_aggregates(user_id, start, end)
    income = totals.get("income", ZERO)
    expenses = totals.get("expense", ZERO)
    debt = _debt_summary(user_id, start, end)
    debt_fees = Decimal(debt["periodFees"])
    net = income - expenses

    commitments, commitment_currencies = _commitment_summary(user_id)
    goals, goal_currencies = _goal_summary(user_id, current_date)
    monthly_committed = (
        commitments["bill"]
        + commitments["subscription"]
        + Decimal(debt["monthlyScheduledPayments"])
        + Decimal(goals["requiredMonthlyContribution"])
    )
    if start is not None:
        effective_start = start
    elif monthly:
        year, month = (int(part) for part in next(iter(monthly)).split("-"))
        effective_start = date(year, month, 1)
    else:
        effective_start = end
    period_days = max((end - effective_start).days + 1, 1)
    monthly_income = income * Decimal("30.4375") / Decimal(period_days)

    opportunities = []
    if categories and expenses > ZERO:
        leading = categories[0]
        share = Decimal(leading["amount"]) / expenses
        if share >= Decimal("0.30"):
            opportunities.append({
                "type": "category_concentration",
                "severity": "medium",
                "title": f"Review {leading['category']} spending",
                "explanation": f"It represents {_percentage(Decimal(leading['amount']), expenses)}% of expenses in this period.",
                "potentialMonthlyAdjustment": None,
            })
    if debt_fees > ZERO:
        opportunities.append({
            "type": "debt_fees",
            "severity": "high",
            "title": "Review recorded debt fees",
            "explanation": f"KES {_money(debt_fees)} in debt fees was recorded during this period.",
            "potentialMonthlyAdjustment": None,
        })
    commitment_ratio = _percentage(monthly_committed, monthly_income)
    if commitment_ratio is not None and Decimal(commitment_ratio) >= Decimal("60"):
        opportunities.append({
            "type": "commitment_pressure",
            "severity": "high",
            "title": "Monthly commitments are high",
            "explanation": f"Planned commitments use about {commitment_ratio}% of average monthly income.",
            "potentialMonthlyAdjustment": None,
        })

    warnings = []
    unsupported = sorted(set(commitment_currencies + goal_currencies))
    if unsupported:
        warnings.append(
            "Commitments or goals in unsupported currencies were excluded: "
            + ", ".join(unsupported)
        )

    return {
        "period": {
            "key": period,
            "start": start.isoformat() if start else None,
            "end": end.isoformat(),
            "currency": "KES",
        },
        "cashFlow": {
            "income": _money(income),
            "expenses": _money(expenses),
            "transactionFees": None,
            "net": _money(net),
            "savingsRate": _percentage(net, income),
        },
        "commitments": {
            "monthlyBills": _money(commitments["bill"]),
            "monthlySubscriptions": _money(commitments["subscription"]),
            "monthlyDebtPayments": debt["monthlyScheduledPayments"],
            "monthlyGoalContributions": goals["requiredMonthlyContribution"],
            "totalMonthlyCommitted": _money(monthly_committed),
            "committedIncomePercentage": commitment_ratio,
        },
        "budget": _budget_summary(user_id),
        "debts": debt,
        "goals": goals,
        "monthlyTrend": [
            {
                "month": month,
                "income": _money(values["income"]),
                "expenses": _money(values["expense"]),
                "net": _money(values["income"] - values["expense"]),
            }
            for month, values in monthly.items()
        ],
        "expenseCategories": categories,
        "dailyActivity": daily,
        "upcoming": _upcoming(user_id, current_date),
        "adjustmentOpportunities": opportunities,
        "coverage": {
            "transactions": True,
            "budgets": True,
            "goals": True,
            "debts": True,
            "bills": True,
            "subscriptions": True,
            "transactionFees": False,
            "debtFees": True,
        },
        "warnings": warnings,
    }

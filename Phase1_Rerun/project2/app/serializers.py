from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.models.budget import Budget, BudgetItem
from app.models.transaction import Transaction
from app.models.user import User
from app.models.debt import Debt, DebtEntry, DebtFeeTerm, DebtSchedule
from app.models.savings_goal import SavingsGoal, SavingsGoalEntry
from app.models.recurring_commitment import (
    CommitmentOccurrence,
    RecurringCommitment,
)
from app.services.savings_goal_service import calculate_savings_goal_plan

def authenticated_user_to_dict(user: User) -> dict[str, object]:
    return {
        "id": str(user.public_id),
        "username": user.username,
        "display_name": user.display_name or user.username,
        "email": user.email,
        "role": user.role or "user",
    }

def transaction_to_dict(transaction: Transaction) -> dict[str, object]:
    category = transaction.category
    payment_method = transaction.payment_method

    return {
        "id": transaction.id,
        "user_id": transaction.user_id,
        "date": transaction.date.isoformat(),
        "description": transaction.description,
        "type": category.type if category else None,
        "category": category.name if category else None,
        "amount": str(transaction.amount),
        "payment_method": payment_method.name if payment_method else None,
    }


def budget_item_to_dict(item: BudgetItem) -> dict[str, object]:
    return {
        "id": item.id,
        "name": item.name,
        "estimatedAmount": float(item.estimated_amount or 0),
        "actualAmount": float(item.actual_amount or 0),
        "checked": item.checked,
        "position": item.position,
    }


def budget_to_dict(budget: Budget) -> dict[str, object]:
    ordered_items = sorted(
        budget.items,
        key=lambda item: (item.position, item.id or 0),
    )
    last_spend = sum(
        (item.actual_amount or Decimal("0") for item in ordered_items),
        Decimal("0"),
    )

    return {
        "id": budget.id,
        "userId": budget.user_id,
        "name": budget.name,
        "category": budget.category or "General",
        "targetAmount": float(budget.target_amount or 0),
        "lastSpend": float(last_spend),
        "lastUsedAt": (
            budget.last_used_at.isoformat()
            if budget.last_used_at
            else None
        ),
        "items": [budget_item_to_dict(item) for item in ordered_items],
    }


def debt_entry_to_dict(entry: DebtEntry) -> dict[str, object]:
    return {
        "id": entry.id,
        "entryType": entry.entry_type,
        "amount": str(entry.amount),
        "occurredOn": entry.occurred_on.isoformat(),
        "feeCategory": entry.fee_category,
        "customFeeName": entry.custom_fee_name,
        "notes": entry.notes,
        "transactionId": entry.transaction_id,
        "createdVia": entry.created_via,
    }


def debt_schedule_to_dict(schedule: DebtSchedule | None) -> dict[str, object] | None:
    if schedule is None:
        return None
    return {
        "frequency": schedule.frequency,
        "intervalCount": schedule.interval_count,
        "installmentAmount": (
            str(schedule.installment_amount)
            if schedule.installment_amount is not None
            else None
        ),
        "nextDueDate": schedule.next_due_date.isoformat(),
        "finalDueDate": (
            schedule.final_due_date.isoformat()
            if schedule.final_due_date
            else None
        ),
    }


def debt_fee_term_to_dict(term: DebtFeeTerm) -> dict[str, object]:
    return {
        "id": term.id,
        "feeCategory": term.fee_category,
        "customFeeName": term.custom_fee_name,
    }


def debt_to_dict(debt: Debt) -> dict[str, object]:
    original_amount = debt.original_amount
    progress = None
    if original_amount and original_amount > 0:
        progress = min(
            100,
            int((debt.paid_amount / original_amount) * 100),
        )

    entries = sorted(
        debt.entries,
        key=lambda entry: (entry.occurred_on, entry.id or 0),
        reverse=True,
    )
    return {
        "id": debt.id,
        "title": debt.title,
        "direction": debt.direction,
        "category": debt.category,
        "counterparty": debt.counterparty,
        "currencyCode": debt.currency_code,
        "trackingKind": debt.tracking_kind,
        "originalAmount": str(original_amount) if original_amount is not None else None,
        "openingBalance": str(debt.opening_balance),
        "amountRepaidBeforeTracking": str(debt.amount_repaid_before_tracking),
        "currentBalance": str(debt.current_balance),
        "paidAmount": str(debt.paid_amount),
        "progress": progress,
        "openedOn": debt.opened_on.isoformat() if debt.opened_on else None,
        "notes": debt.notes,
        "hasInterest": debt.has_interest,
        "statedInterestRate": (
            str(debt.stated_interest_rate)
            if debt.stated_interest_rate is not None
            else None
        ),
        "interestPeriod": debt.interest_period,
        "status": debt.status,
        "createdVia": debt.created_via,
        "schedule": debt_schedule_to_dict(debt.schedule),
        "feeTerms": [
            debt_fee_term_to_dict(term)
            for term in sorted(debt.fee_terms, key=lambda term: term.id or 0)
        ],
        "entries": [debt_entry_to_dict(entry) for entry in entries],
        "createdAt": debt.created_at.isoformat() if debt.created_at else None,
        "updatedAt": debt.updated_at.isoformat() if debt.updated_at else None,
    }


def savings_goal_entry_to_dict(entry: SavingsGoalEntry) -> dict[str, object]:
    return {
        "id": entry.id,
        "entryType": entry.entry_type,
        "amount": str(entry.amount),
        "occurredOn": entry.occurred_on.isoformat(),
        "notes": entry.notes,
        "createdVia": entry.created_via,
    }


def savings_goal_to_dict(goal: SavingsGoal) -> dict[str, object]:
    plan = calculate_savings_goal_plan(goal)
    target_amount = Decimal(goal.target_amount)
    current_savings = goal.current_savings
    progress = min(
        100,
        int(
            ((current_savings / target_amount) * 100).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP,
            )
        ),
    )
    entries = sorted(
        goal.entries,
        key=lambda entry: (entry.occurred_on, entry.id or 0),
        reverse=True,
    )
    return {
        "id": goal.id,
        "name": goal.name,
        "targetAmount": str(target_amount),
        "currentSavings": str(current_savings),
        "remainingAmount": str(plan.remaining_amount),
        "targetDate": goal.target_date.isoformat(),
        "contributionFrequency": goal.contribution_frequency,
        "suggestedContribution": str(plan.suggested_contribution),
        "remainingPeriods": plan.remaining_periods,
        "progress": progress,
        "overdue": plan.overdue,
        "targetReached": plan.target_reached,
        "currencyCode": goal.currency_code,
        "notes": goal.notes,
        "createdVia": goal.created_via,
        "entries": [savings_goal_entry_to_dict(entry) for entry in entries],
        "createdAt": goal.created_at.isoformat() if goal.created_at else None,
        "updatedAt": goal.updated_at.isoformat() if goal.updated_at else None,
    }


def commitment_occurrence_to_dict(
    occurrence: CommitmentOccurrence,
) -> dict[str, object]:
    return {
        "id": occurrence.id,
        "resolution": occurrence.resolution,
        "dueDate": occurrence.due_date.isoformat(),
        "expectedAmount": str(occurrence.expected_amount),
        "actualAmount": (
            str(occurrence.actual_amount)
            if occurrence.actual_amount is not None
            else None
        ),
        "resolvedOn": occurrence.resolved_on.isoformat(),
        "notes": occurrence.notes,
        "createdVia": occurrence.created_via,
    }


def recurring_commitment_to_dict(
    commitment: RecurringCommitment,
) -> dict[str, object]:
    occurrences = sorted(
        commitment.occurrences,
        key=lambda item: (item.due_date, item.id or 0),
        reverse=True,
    )
    return {
        "id": commitment.id,
        "kind": commitment.kind,
        "name": commitment.name,
        "provider": commitment.provider,
        "category": commitment.category,
        "amount": str(commitment.amount),
        "amountKind": commitment.amount_kind,
        "currencyCode": commitment.currency_code,
        "nextDueDate": commitment.next_due_date.isoformat(),
        "frequency": commitment.frequency,
        "customIntervalDays": commitment.custom_interval_days,
        "autoRenews": commitment.auto_renews,
        "status": commitment.status,
        "cancelledAt": (
            commitment.cancelled_at.isoformat()
            if commitment.cancelled_at
            else None
        ),
        "overdue": (
            commitment.status == "active"
            and commitment.next_due_date < date.today()
        ),
        "notes": commitment.notes,
        "createdVia": commitment.created_via,
        "occurrences": [
            commitment_occurrence_to_dict(item) for item in occurrences
        ],
        "createdAt": (
            commitment.created_at.isoformat() if commitment.created_at else None
        ),
        "updatedAt": (
            commitment.updated_at.isoformat() if commitment.updated_at else None
        ),
    }

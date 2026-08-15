from decimal import Decimal

from app.models.budget import Budget, BudgetItem
from app.models.transaction import Transaction
from app.models.user import User

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

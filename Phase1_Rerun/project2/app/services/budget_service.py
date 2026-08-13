from datetime import UTC, datetime
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.extensions import db
from app.models.budget import Budget, BudgetItem


class BudgetItemData(TypedDict):
    name: str
    estimated_amount: Decimal
    checked: bool


def _budget_select():
    return select(Budget).options(selectinload(Budget.items))


def get_budget_for_user(user_id: int, budget_id: int) -> Budget | None:
    statement = _budget_select().where(
        Budget.id == budget_id,
        Budget.user_id == user_id,
    )
    return db.session.scalar(statement)


def get_budgets_for_user(user_id: int) -> list[Budget]:
    statement = (
        _budget_select()
        .where(Budget.user_id == user_id)
        .order_by(
            func.coalesce(
                Budget.last_used_at,
                Budget.updated_at,
                Budget.created_at,
            ).desc(),
            Budget.id.desc(),
        )
    )
    return list(db.session.scalars(statement).all())


def create_budget_for_user(
    user_id: int,
    name: str,
    category: str,
    target_amount: Decimal,
    items: list[BudgetItemData],
) -> Budget:
    try:
        budget = Budget(
            user_id=user_id,
            name=name,
            category=category,
            target_amount=target_amount,
            last_used_at=datetime.now(UTC),
            items=[
                BudgetItem(
                    name=item["name"],
                    estimated_amount=item["estimated_amount"],
                    checked=False,
                    position=index,
                )
                for index, item in enumerate(items)
            ],
        )
        db.session.add(budget)
        db.session.commit()

        saved_budget = get_budget_for_user(user_id, budget.id)
        if saved_budget is None:
            raise RuntimeError("Created budget could not be reloaded")
        return saved_budget
    except Exception:
        db.session.rollback()
        raise


def update_budget_for_user(
    user_id: int,
    budget_id: int,
    name: str,
    category: str,
    target_amount: Decimal,
    items: list[BudgetItemData],
) -> Budget | None:
    try:
        budget = get_budget_for_user(user_id, budget_id)
        if budget is None:
            return None

        budget.name = name
        budget.category = category
        budget.target_amount = target_amount
        budget.items = [
            BudgetItem(
                name=item["name"],
                estimated_amount=item["estimated_amount"],
                checked=item.get("checked", False),
                position=index,
            )
            for index, item in enumerate(items)
        ]
        db.session.commit()

        return get_budget_for_user(user_id, budget_id)
    except Exception:
        db.session.rollback()
        raise


def delete_budget_for_user(user_id: int, budget_id: int) -> bool:
    try:
        budget = get_budget_for_user(user_id, budget_id)
        if budget is None:
            return False

        db.session.delete(budget)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        raise


def update_budget_item_checked_for_user(
    user_id: int,
    item_id: int,
    checked: bool,
) -> BudgetItem | None:
    try:
        statement = (
            select(BudgetItem)
            .join(Budget)
            .options(joinedload(BudgetItem.budget))
            .where(
                BudgetItem.id == item_id,
                Budget.user_id == user_id,
            )
        )
        item = db.session.scalar(statement)
        if item is None:
            return None

        item.checked = checked
        item.budget.last_used_at = datetime.now(UTC)
        db.session.commit()
        return item
    except Exception:
        db.session.rollback()
        raise

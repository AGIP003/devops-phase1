from datetime import date
from decimal import Decimal


from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from app.extensions import db
from app.models.transaction import Transaction
from app.models.payment_method import PaymentMethod
from app.services.category_service import get_or_create_category


def _transaction_select():
    return select(Transaction).options(
        selectinload(Transaction.category),
        selectinload(Transaction.payment_method),
    )

def list_transactions_for_user(user_id: int, query: str | None = None) -> list[Transaction]:
    statement = (
        _transaction_select()
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
        )
        .order_by(Transaction.date.desc())
    )

    if query:
        statement = statement.where(
            func.coalesce(Transaction.description, "").ilike(f"%{query}%")
        )

    return list(db.session.scalars(statement).all())


def get_transaction_for_user(user_id: int, transaction_id: int) -> Transaction | None:
    statement = (
        _transaction_select()
        .where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
        )
    )
    return db.session.scalar(statement)

def _get_payment_method_by_name(payment_method_name: str) -> PaymentMethod | None:
    statement = (
        select(PaymentMethod)
        .where(
            func.lower(PaymentMethod.name) == payment_method_name.lower()
        )
    )

    return db.session.scalar(statement)

def create_transaction_for_user(
    user_id: int,
    category_name: str,
    transaction_type: str,
    payment_method_name: str,
    amount: Decimal,
    transaction_date: date,
    description: str,
) -> Transaction:
    try:
        payment_method = _get_payment_method_by_name(payment_method_name)

        if payment_method is None:
            raise ValueError(
                f"Payment method '{payment_method_name}' not found"
            )

        category = get_or_create_category(
            name=category_name,
            type=transaction_type,
            user_id=user_id,
        )

        transaction = Transaction(
            user_id=user_id,
            category=category,
            payment_method=payment_method,
            amount=amount,
            date=transaction_date,
            description=description,
        )

        db.session.add(transaction)
        db.session.commit()

        return transaction

    except Exception:
        db.session.rollback()
        raise


def update_transaction_for_user(
    user_id: int,
    transaction_id: int,
    *,
    amount: Decimal | None = None,
    transaction_date: date | None = None,
    description: str | None = None,
    category_name: str | None = None,
    transaction_type: str | None = None,
    payment_method_name: str | None = None,
) -> Transaction | None:
    try:
        if all(
            value is None
            for value in (
                amount,
                transaction_date,
                description,
                category_name,
                payment_method_name,
            )
        ):
            raise ValueError("No fields to update")

        transaction = get_transaction_for_user(user_id, transaction_id)
        if transaction is None:
            return None

        if amount is not None:
            transaction.amount = amount

        if transaction_date is not None:
            transaction.date = transaction_date

        if description is not None:
            transaction.description = description

        if category_name is not None:
            if transaction_type is None:
                raise ValueError(
                    "Transaction type is required when changing category"
                )

            category = get_or_create_category(
                name=category_name,
                type=transaction_type,
                user_id=user_id,
            )
            transaction.category = category

        if payment_method_name is not None:
            payment_method = _get_payment_method_by_name(payment_method_name)

            if payment_method is None:
                raise ValueError(
                    f"Payment method '{payment_method_name}' not found"
                )

            transaction.payment_method = payment_method

        db.session.commit()
        return transaction

    except Exception:
        db.session.rollback()
        raise

def soft_delete_transaction_for_user(user_id: int, transaction_id: int) -> bool:
    try:
        transaction = get_transaction_for_user(user_id, transaction_id)

        if transaction is None:
            return False

        transaction.soft_delete()
        db.session.commit()

        return True

    except Exception:
        db.session.rollback()
        raise

def list_all_transactions() -> list[Transaction]:
    statement = (
        _transaction_select()
        .where(Transaction.deleted_at.is_(None))
        .order_by(Transaction.date.desc())
    )

    return list(db.session.scalars(statement).all())

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
        selectinload(Transaction.import_record),
    )


def normalize_merchant_name(value: str | None) -> str | None:
    """Normalize an optional merchant without inventing one from description."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Merchant name must be text")
    clean = " ".join(value.strip().split())
    if not clean:
        return None
    if len(clean) > 150:
        raise ValueError("Merchant name cannot exceed 150 characters")
    return clean

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


def build_transaction_for_user(
    user_id: int,
    category_name: str,
    transaction_type: str,
    payment_method_name: str,
    amount: Decimal,
    transaction_date: date,
    description: str,
    merchant_name: str | None = None,
) -> Transaction:
    """Build a transaction without committing so a caller can compose one ACID unit."""
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
        merchant_name=normalize_merchant_name(merchant_name),
    )
    db.session.add(transaction)
    return transaction

def create_transaction_for_user(
    user_id: int,
    category_name: str,
    transaction_type: str,
    payment_method_name: str,
    amount: Decimal,
    transaction_date: date,
    description: str,
    merchant_name: str | None = None,
) -> Transaction:
    try:
        transaction = build_transaction_for_user(
            user_id=user_id,
            category_name=category_name,
            transaction_type=transaction_type,
            payment_method_name=payment_method_name,
            amount=amount,
            transaction_date=transaction_date,
            description=description,
            merchant_name=merchant_name,
        )
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
    merchant_name: str | None = None,
    merchant_supplied: bool = False,
) -> Transaction | None:
    try:
        if not merchant_supplied and all(
            value is None
            for value in (
                amount,
                transaction_date,
                description,
                category_name,
                payment_method_name,
                merchant_name,
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

        if merchant_supplied:
            transaction.merchant_name = normalize_merchant_name(merchant_name)

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

from sqlalchemy import event, select
from sqlalchemy.orm import selectinload

from app import create_app
from app.extensions import db
from app.models.transaction import Transaction


app = create_app()
query_count = {"count": 0}


with app.app_context():

    @event.listens_for(db.engine, "before_cursor_execute")
    def count_queries(
        connection,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ):
        query_count["count"] += 1

    lazy_statement = (
        select(Transaction)
        .where(
            Transaction.user_id == 1,
            Transaction.deleted_at.is_(None),
        )
    )
    query_count["count"] = 0
    transactions = list(
        db.session.scalars(lazy_statement).all()
    )
    for transaction in transactions:
        _ = transaction.category
        _ = transaction.payment_method
    print("Transactions:", len(transactions))
    print("Lazy loading queries:", query_count["count"])

    db.session.remove()
    query_count["count"] = 0

    eager_statement = (
        select(Transaction)
        .options(
            selectinload(Transaction.category),
            selectinload(Transaction.payment_method),
        )
        .where(
            Transaction.user_id == 1,
            Transaction.deleted_at.is_(None),
        )
    )

    eager_transactions = list(
        db.session.scalars(eager_statement).all()
    )
    for transaction in eager_transactions:
        _ = transaction.category
        _ = transaction.payment_method

    print("Eager-loaded transactions:", len(eager_transactions))
    print("Eager-loading queries:", query_count["count"])

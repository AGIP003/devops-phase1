from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimeStampMixin


class TransactionImport(TimeStampMixin, Base):
    """Minimal provenance for a transaction imported from a provider message.

    Raw SMS text, wallet balances, phone numbers and account numbers are
    intentionally not persisted.
    """

    __tablename__ = "transaction_imports"
    __table_args__ = (
        UniqueConstraint(
            "transaction_id",
            name="uq_transaction_imports_transaction_id",
        ),
        UniqueConstraint(
            "user_id",
            "provider",
            "external_reference",
            name="uq_transaction_imports_user_provider_reference",
        ),
        UniqueConstraint(
            "user_id",
            "message_fingerprint",
            name="uq_transaction_imports_user_fingerprint",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    transaction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    external_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    message_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    provider_transaction_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    fee: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    transaction = relationship("Transaction", back_populates="import_record")

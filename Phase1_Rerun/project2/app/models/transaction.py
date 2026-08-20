from datetime import UTC, date, datetime
from decimal import Decimal
from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.models.base import Base, TimeStampMixin, SoftDeleteMixin

class Transaction(TimeStampMixin, SoftDeleteMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_transactions_category_id", "category_id"),
        Index("idx_transactions_date", "date"),
        Index("idx_transactions_user_date", "user_id", "date"),
        Index("idx_transactions_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    payment_method_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payment_methods.id"), nullable=True
    )

    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    payment_method = relationship("PaymentMethod", back_populates="transactions")
    import_record = relationship(
        "TransactionImport",
        back_populates="transaction",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    def soft_delete(self):
        self.deleted_at = datetime.now(UTC)

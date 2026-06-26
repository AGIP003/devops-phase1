from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Integer, Numeric, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from app.models.base import Base, TimeStampMixin, SoftDeleteMixin

class Transaction(TimeStampMixin, SoftDeleteMixin, Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    payment_method_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payment_methods.id"), nullable=True
    )
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PaymentMethodGroup(Base):
    __tablename__ = "payment_method_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    payment_methods = relationship(
        "PaymentMethod",
        back_populates="group",
        lazy="select",
    )


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    group_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("payment_method_groups.id"),
        nullable=True,
    )

    group = relationship("PaymentMethodGroup", back_populates="payment_methods")
    transactions = relationship(
        "Transaction",
        back_populates="payment_method",
        lazy="select",
    )

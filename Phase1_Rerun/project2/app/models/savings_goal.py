from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimeStampMixin


class SavingsGoal(TimeStampMixin, SoftDeleteMixin, Base):
    __tablename__ = "savings_goals"
    __table_args__ = (
        CheckConstraint("target_amount > 0", name="ck_savings_goals_target_amount"),
        CheckConstraint(
            "contribution_frequency IN ('weekly', 'fortnightly', 'monthly')",
            name="ck_savings_goals_frequency",
        ),
        UniqueConstraint(
            "user_id",
            "created_via",
            "external_reference",
            name="uq_savings_goals_user_source_reference",
        ),
        Index("idx_savings_goals_user_target", "user_id", "target_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    contribution_frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="KES",
        server_default="KES",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_via: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="manual",
        server_default="manual",
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )

    user = relationship("User", back_populates="savings_goals")
    entries: Mapped[list[SavingsGoalEntry]] = relationship(
        "SavingsGoalEntry",
        back_populates="goal",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def current_savings(self) -> Decimal:
        balance = Decimal("0")
        for entry in self.entries:
            amount = Decimal(entry.amount)
            balance += amount if entry.entry_type == "contribution" else -amount
        return max(balance, Decimal("0"))

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)


class SavingsGoalEntry(TimeStampMixin, Base):
    __tablename__ = "savings_goal_entries"
    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('contribution', 'withdrawal')",
            name="ck_savings_goal_entries_type",
        ),
        CheckConstraint("amount > 0", name="ck_savings_goal_entries_amount"),
        UniqueConstraint(
            "goal_id",
            "created_via",
            "external_reference",
            name="uq_savings_goal_entries_source_reference",
        ),
        Index(
            "idx_savings_goal_entries_goal_date",
            "goal_id",
            "occurred_on",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("savings_goals.id", ondelete="CASCADE"),
        nullable=False,
    )
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_via: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="manual",
        server_default="manual",
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )

    goal: Mapped[SavingsGoal] = relationship("SavingsGoal", back_populates="entries")

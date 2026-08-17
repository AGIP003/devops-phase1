from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimeStampMixin


class RecurringCommitment(TimeStampMixin, SoftDeleteMixin, Base):
    """A recurring bill or subscription owned by one MoneyTiq user."""

    __tablename__ = "recurring_commitments"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('bill', 'subscription')",
            name="ck_recurring_commitments_kind",
        ),
        CheckConstraint("amount > 0", name="ck_recurring_commitments_amount"),
        CheckConstraint(
            "amount_kind IN ('fixed', 'estimated')",
            name="ck_recurring_commitments_amount_kind",
        ),
        CheckConstraint(
            "frequency IN ('weekly', 'monthly', 'quarterly', 'termly', "
            "'yearly', 'custom')",
            name="ck_recurring_commitments_frequency",
        ),
        CheckConstraint(
            "(frequency = 'custom' AND custom_interval_days IS NOT NULL "
            "AND custom_interval_days > 0) OR "
            "(frequency <> 'custom' AND custom_interval_days IS NULL)",
            name="ck_recurring_commitments_custom_interval",
        ),
        CheckConstraint(
            "status IN ('active', 'cancelled')",
            name="ck_recurring_commitments_status",
        ),
        CheckConstraint(
            "recurrence_anchor_day BETWEEN 1 AND 31",
            name="ck_recurring_commitments_anchor_day",
        ),
        CheckConstraint(
            "(kind = 'subscription' AND auto_renews IS NOT NULL) OR "
            "(kind = 'bill' AND auto_renews IS NULL)",
            name="ck_recurring_commitments_auto_renews",
        ),
        UniqueConstraint(
            "user_id",
            "created_via",
            "external_reference",
            name="uq_recurring_commitments_user_source_reference",
        ),
        Index(
            "idx_recurring_commitments_user_due",
            "user_id",
            "status",
            "next_due_date",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    amount_kind: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="fixed",
        server_default="fixed",
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="KES",
        server_default="KES",
    )
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    custom_interval_days: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
    )
    recurrence_anchor_day: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    auto_renews: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    user = relationship("User", back_populates="recurring_commitments")
    occurrences: Mapped[list[CommitmentOccurrence]] = relationship(
        "CommitmentOccurrence",
        back_populates="commitment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)


class CommitmentOccurrence(TimeStampMixin, Base):
    """A historical due-cycle record that the owner may correct."""

    __tablename__ = "commitment_occurrences"
    __table_args__ = (
        CheckConstraint(
            "resolution IN ('paid', 'skipped')",
            name="ck_commitment_occurrences_resolution",
        ),
        CheckConstraint(
            "expected_amount > 0",
            name="ck_commitment_occurrences_expected_amount",
        ),
        CheckConstraint(
            "(resolution = 'paid' AND actual_amount IS NOT NULL "
            "AND actual_amount > 0) OR "
            "(resolution = 'skipped' AND actual_amount IS NULL)",
            name="ck_commitment_occurrences_actual_amount",
        ),
        UniqueConstraint(
            "commitment_id",
            "created_via",
            "external_reference",
            name="uq_commitment_occurrences_source_reference",
        ),
        Index(
            "idx_commitment_occurrences_commitment_due",
            "commitment_id",
            "due_date",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    commitment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("recurring_commitments.id", ondelete="CASCADE"),
        nullable=False,
    )
    resolution: Mapped[str] = mapped_column(String(20), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    actual_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )
    resolved_on: Mapped[date] = mapped_column(Date, nullable=False)
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

    commitment: Mapped[RecurringCommitment] = relationship(
        "RecurringCommitment",
        back_populates="occurrences",
    )

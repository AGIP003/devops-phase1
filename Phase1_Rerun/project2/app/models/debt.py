from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Boolean,
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


BALANCE_INCREASE_ENTRY_TYPES = {
    "interest",
    "fee",
    "adjustment_increase",
}
BALANCE_DECREASE_ENTRY_TYPES = {
    "repayment",
    "adjustment_decrease",
}


class Debt(TimeStampMixin, SoftDeleteMixin, Base):
    __tablename__ = "debts"
    __table_args__ = (
        CheckConstraint(
            "direction IN ('i_owe', 'owed_to_me')",
            name="ck_debts_direction",
        ),
        CheckConstraint(
            "tracking_kind IN ('new', 'existing')",
            name="ck_debts_tracking_kind",
        ),
        CheckConstraint(
            "status IN ('active', 'settled', 'written_off', 'cancelled')",
            name="ck_debts_status",
        ),
        CheckConstraint("opening_balance >= 0", name="ck_debts_opening_balance"),
        CheckConstraint(
            "original_amount IS NULL OR original_amount > 0",
            name="ck_debts_original_amount",
        ),
        CheckConstraint(
            "amount_repaid_before_tracking >= 0",
            name="ck_debts_prior_repayment",
        ),
        CheckConstraint(
            "stated_interest_rate IS NULL OR stated_interest_rate > 0",
            name="ck_debts_interest_rate",
        ),
        UniqueConstraint(
            "user_id",
            "created_via",
            "external_reference",
            name="uq_debts_user_source_reference",
        ),
        Index("idx_debts_user_status", "user_id", "status"),
        Index("idx_debts_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(140), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    counterparty: Mapped[str | None] = mapped_column(String(100), nullable=True)
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="KES",
        server_default="KES",
    )
    tracking_kind: Mapped[str] = mapped_column(String(12), nullable=False)
    original_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    amount_repaid_before_tracking: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    opened_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    stated_interest_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )
    has_interest: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    interest_period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
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

    user = relationship("User", back_populates="debts")
    schedule: Mapped[DebtSchedule | None] = relationship(
        "DebtSchedule",
        back_populates="debt",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    fee_terms: Mapped[list[DebtFeeTerm]] = relationship(
        "DebtFeeTerm",
        back_populates="debt",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    entries: Mapped[list[DebtEntry]] = relationship(
        "DebtEntry",
        back_populates="debt",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def current_balance(self) -> Decimal:
        balance = Decimal(self.opening_balance)
        for entry in self.entries:
            amount = Decimal(entry.amount)
            if entry.entry_type in BALANCE_INCREASE_ENTRY_TYPES:
                balance += amount
            elif entry.entry_type in BALANCE_DECREASE_ENTRY_TYPES:
                balance -= amount
        return max(balance, Decimal("0"))

    @property
    def paid_amount(self) -> Decimal:
        recorded_repayments = sum(
            (
                Decimal(entry.amount)
                for entry in self.entries
                if entry.entry_type == "repayment"
            ),
            Decimal("0"),
        )
        return Decimal(self.amount_repaid_before_tracking) + recorded_repayments

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)


class DebtSchedule(TimeStampMixin, Base):
    __tablename__ = "debt_schedules"
    __table_args__ = (
        CheckConstraint(
            "frequency IN ('one_time', 'daily', 'weekly', 'monthly')",
            name="ck_debt_schedules_frequency",
        ),
        CheckConstraint("interval_count > 0", name="ck_debt_schedules_interval"),
        CheckConstraint(
            "installment_amount IS NULL OR installment_amount > 0",
            name="ck_debt_schedules_installment",
        ),
        UniqueConstraint("debt_id", name="uq_debt_schedules_debt_id"),
        Index("idx_debt_schedules_next_due", "next_due_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    debt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("debts.id", ondelete="CASCADE"),
        nullable=False,
    )
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    interval_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    installment_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    final_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    debt: Mapped[Debt] = relationship("Debt", back_populates="schedule")


class DebtFeeTerm(TimeStampMixin, Base):
    __tablename__ = "debt_fee_terms"
    __table_args__ = (
        CheckConstraint(
            "fee_category IN ('processing', 'origination', 'late_payment', "
            "'insurance', 'service', 'restructuring', 'legal_collection', 'other')",
            name="ck_debt_fee_terms_category",
        ),
        CheckConstraint(
            "fee_category <> 'other' OR custom_fee_name IS NOT NULL",
            name="ck_debt_fee_terms_other_name",
        ),
        UniqueConstraint(
            "debt_id",
            "fee_category",
            "custom_fee_name",
            name="uq_debt_fee_terms_debt_category_name",
        ),
        Index("idx_debt_fee_terms_debt_id", "debt_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    debt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("debts.id", ondelete="CASCADE"),
        nullable=False,
    )
    fee_category: Mapped[str] = mapped_column(String(32), nullable=False)
    custom_fee_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    debt: Mapped[Debt] = relationship("Debt", back_populates="fee_terms")


class DebtEntry(TimeStampMixin, Base):
    __tablename__ = "debt_entries"
    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('repayment', 'interest', 'fee', "
            "'adjustment_increase', 'adjustment_decrease')",
            name="ck_debt_entries_type",
        ),
        CheckConstraint("amount > 0", name="ck_debt_entries_amount"),
        CheckConstraint(
            "fee_category IS NULL OR fee_category IN "
            "('processing', 'origination', 'late_payment', 'insurance', "
            "'service', 'restructuring', 'legal_collection', 'other')",
            name="ck_debt_entries_fee_category",
        ),
        CheckConstraint(
            "entry_type <> 'fee' OR fee_category IS NOT NULL",
            name="ck_debt_entries_fee_required",
        ),
        CheckConstraint(
            "entry_type = 'fee' OR "
            "(fee_category IS NULL AND custom_fee_name IS NULL)",
            name="ck_debt_entries_fee_fields",
        ),
        CheckConstraint(
            "fee_category <> 'other' OR custom_fee_name IS NOT NULL",
            name="ck_debt_entries_other_fee_name",
        ),
        UniqueConstraint("transaction_id", name="uq_debt_entries_transaction_id"),
        UniqueConstraint(
            "debt_id",
            "created_via",
            "external_reference",
            name="uq_debt_entries_source_reference",
        ),
        Index("idx_debt_entries_debt_date", "debt_id", "occurred_on"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    debt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("debts.id", ondelete="CASCADE"),
        nullable=False,
    )
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    fee_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    custom_fee_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
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

    debt: Mapped[Debt] = relationship("Debt", back_populates="entries")
    transaction = relationship("Transaction")

from datetime import date, datetime
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
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimeStampMixin


class ProviderFinancingEvent(TimeStampMixin, Base):
    """Minimal, non-raw record of a provider financing notice.

    Principal draws and repayments are retained for explanation but are not
    treated as fresh spending. Only explicit financing charges are included in
    expense analytics, preventing a financed purchase and its repayment from
    being counted twice.
    """

    __tablename__ = "provider_financing_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('draw', 'repayment')",
            name="ck_provider_financing_events_type",
        ),
        UniqueConstraint(
            "user_id",
            "provider",
            "external_reference",
            "event_type",
            name="uq_provider_financing_events_reference",
        ),
        UniqueConstraint(
            "user_id",
            "message_fingerprint",
            name="uq_provider_financing_events_fingerprint",
        ),
        Index(
            "idx_provider_financing_events_user_date",
            "user_id",
            "recorded_on",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    external_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    message_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(24), nullable=False)
    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    financing_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    daily_maintenance_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    outstanding_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    recorded_on: Mapped[date] = mapped_column(Date, nullable=False)
    settled_in_full: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    user = relationship("User", back_populates="provider_financing_events")

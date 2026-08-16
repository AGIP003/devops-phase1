from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ForexRate(Base):
    """A validated, provider-specific rate retained as last-known-good data."""

    __tablename__ = "forex_rates"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "base_currency",
            "quote_currency",
            "rate_date",
            name="uq_forex_rates_provider_pair_date",
        ),
        Index(
            "idx_forex_rates_provider_base_date",
            "provider",
            "base_currency",
            "rate_date",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    quote_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(24, 12), nullable=False)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

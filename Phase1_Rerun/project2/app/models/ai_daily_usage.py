from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Integer, Numeric, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AIDailyUsage(Base):
    """Aggregate AI costs without storing prompts or finance content."""

    __tablename__ = "ai_daily_usage"

    usage_date: Mapped[date] = mapped_column(Date, primary_key=True)
    reserved_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 8),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    estimated_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 8),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    input_tokens: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    cached_input_tokens: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    output_tokens: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    completed_requests: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    failed_requests: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

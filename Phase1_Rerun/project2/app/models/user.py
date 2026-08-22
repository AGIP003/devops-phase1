from datetime import datetime
import uuid

from sqlalchemy import Uuid, func, text, Integer, String, DateTime, BigInteger, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.models.base import Base, TimeStampMixin

class User(TimeStampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint(
            "public_id",
            name="uq_users_public_id",
        ),
)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        server_default=func.gen_random_uuid(),
    )
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=True)
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    telegram_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, unique=True
    )
    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    auth_identities: Mapped[list["AuthIdentity"]] = relationship(
        "AuthIdentity",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan", lazy="select")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan", lazy="select")
    debts = relationship("Debt", back_populates="user", cascade="all, delete-orphan", lazy="select")
    savings_goals = relationship("SavingsGoal", back_populates="user", cascade="all, delete-orphan", lazy="select")
    recurring_commitments = relationship("RecurringCommitment", back_populates="user", cascade="all, delete-orphan", lazy="select")
    provider_financing_events = relationship(
        "ProviderFinancingEvent",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select",
    )
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan", lazy="select")

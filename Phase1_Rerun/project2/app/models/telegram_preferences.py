from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base


class TelegramUserPreferences(Base):
    __tablename__ = "telegram_user_preferences"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )
    default_payment_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="m-pesa"
    )
    category_aliases: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
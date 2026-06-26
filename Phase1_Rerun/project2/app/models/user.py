from sqlalchemy import Integer, String, DateTime, BigInteger
from sqlalchemy.orm import mapped_column, Mapped
from app.models.base import Base, TimeStampMixin

class User(TimeStampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=True)
    last_login: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=True, unique=True)

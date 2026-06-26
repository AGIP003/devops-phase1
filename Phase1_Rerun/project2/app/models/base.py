from datetime import datetime
from app.extensions import db
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import DateTime

class Base(DeclarativeBase):
    pass

class TimeStampMixin:                                 
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

class SoftDeleteMixin:
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime, default=None, nullable=True
    )
from datetime import UTC, datetime
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.models.base import Base

class Category(Base):
    __tablename__="categories"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "name",
            name="categories_user_id_name_key",
        ),
        Index("idx_categories_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=True,
    )

    transactions = relationship(
        "Transaction",
        back_populates="category",
        lazy="select"
    )
    user = relationship("User", back_populates="categories")

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimeStampMixin


class QuotationProject(TimeStampMixin, Base):
    __tablename__ = "quotation_projects"
    __table_args__ = (
        Index("idx_quotation_projects_user_updated", "user_id", "updated_at"),
        CheckConstraint(
            "status IN ('comparing', 'supplier_selected', 'archived')",
            name="ck_quotation_projects_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="KES",
        server_default=text("'KES'"),
    )
    status: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        default="comparing",
        server_default=text("'comparing'"),
    )

    user = relationship("User", back_populates="quotation_projects")
    items: Mapped[list["QuotationItem"]] = relationship(
        "QuotationItem",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="QuotationItem.position",
    )
    quotations: Mapped[list["SupplierQuotation"]] = relationship(
        "SupplierQuotation",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SupplierQuotation.id",
    )


class QuotationItem(TimeStampMixin, Base):
    __tablename__ = "quotation_items"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "name",
            name="uq_quotation_items_project_name",
        ),
        Index("idx_quotation_items_project_position", "project_id", "position"),
        CheckConstraint("quantity > 0", name="ck_quotation_items_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quotation_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    project: Mapped[QuotationProject] = relationship(
        "QuotationProject",
        back_populates="items",
    )
    prices: Mapped[list["SupplierQuotationPrice"]] = relationship(
        "SupplierQuotationPrice",
        back_populates="item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SupplierQuotation(TimeStampMixin, Base):
    __tablename__ = "supplier_quotations"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "supplier",
            name="uq_supplier_quotations_project_supplier",
        ),
        Index("idx_supplier_quotations_project_id", "project_id"),
        Index(
            "uq_supplier_quotations_one_preferred",
            "project_id",
            unique=True,
            postgresql_where=text("preferred = true"),
        ),
        CheckConstraint(
            "tax_mode IN ('included', 'excluded', 'none')",
            name="ck_supplier_quotations_tax_mode",
        ),
        CheckConstraint("delivery_cost >= 0", name="ck_supplier_quotations_delivery_cost"),
        CheckConstraint("discount >= 0", name="ck_supplier_quotations_discount"),
        CheckConstraint("tax_rate >= 0", name="ck_supplier_quotations_tax_rate"),
        CheckConstraint(
            "delivery_days IS NULL OR delivery_days >= 0",
            name="ck_supplier_quotations_delivery_days",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quotation_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    supplier: Mapped[str] = mapped_column(String(100), nullable=False)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, server_default=text("0")
    )
    discount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, server_default=text("0")
    )
    tax_mode: Mapped[str] = mapped_column(
        String(12), nullable=False, default="included", server_default=text("'included'")
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0, server_default=text("0")
    )
    delivery_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(String(150), nullable=True)
    preferred: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

    project: Mapped[QuotationProject] = relationship(
        "QuotationProject",
        back_populates="quotations",
    )
    prices: Mapped[list["SupplierQuotationPrice"]] = relationship(
        "SupplierQuotationPrice",
        back_populates="quotation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SupplierQuotationPrice(TimeStampMixin, Base):
    __tablename__ = "supplier_quotation_prices"
    __table_args__ = (
        UniqueConstraint(
            "quotation_id",
            "item_id",
            name="uq_supplier_quotation_prices_quote_item",
        ),
        Index("idx_supplier_quotation_prices_item_id", "item_id"),
        CheckConstraint("unit_price >= 0", name="ck_supplier_quotation_prices_price"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quotation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("supplier_quotations.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quotation_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    quotation: Mapped[SupplierQuotation] = relationship(
        "SupplierQuotation",
        back_populates="prices",
    )
    item: Mapped[QuotationItem] = relationship(
        "QuotationItem",
        back_populates="prices",
    )

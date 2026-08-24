from datetime import date
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.quotation import (
    QuotationItem,
    QuotationProject,
    SupplierQuotation,
    SupplierQuotationPrice,
)


class QuotationConflictError(ValueError):
    """A project already contains an item or supplier with that name."""


def _project_select():
    return select(QuotationProject).options(
        selectinload(QuotationProject.items),
        selectinload(QuotationProject.quotations).selectinload(
            SupplierQuotation.prices
        ),
    )


def get_quotation_project_for_user(
    user_id: int,
    project_id: int,
) -> QuotationProject | None:
    return db.session.scalar(
        _project_select().where(
            QuotationProject.id == project_id,
            QuotationProject.user_id == user_id,
        )
    )


def list_quotation_projects_for_user(user_id: int) -> list[QuotationProject]:
    statement = (
        _project_select()
        .where(QuotationProject.user_id == user_id)
        .order_by(
            func.coalesce(
                QuotationProject.updated_at,
                QuotationProject.created_at,
            ).desc(),
            QuotationProject.id.desc(),
        )
    )
    return list(db.session.scalars(statement).unique().all())


def create_quotation_project_for_user(
    user_id: int,
    *,
    title: str,
    category: str,
    notes: str | None,
    currency_code: str,
) -> QuotationProject:
    try:
        project = QuotationProject(
            user_id=user_id,
            title=title,
            category=category,
            notes=notes,
            currency_code=currency_code,
        )
        db.session.add(project)
        db.session.commit()
        return get_quotation_project_for_user(user_id, project.id)
    except Exception:
        db.session.rollback()
        raise


def update_quotation_project_for_user(
    user_id: int,
    project_id: int,
    *,
    title: str,
    category: str,
    notes: str | None,
    status: str,
) -> QuotationProject | None:
    try:
        project = get_quotation_project_for_user(user_id, project_id)
        if project is None:
            return None
        project.title = title
        project.category = category
        project.notes = notes
        project.status = status
        db.session.commit()
        return get_quotation_project_for_user(user_id, project_id)
    except Exception:
        db.session.rollback()
        raise


def delete_quotation_project_for_user(user_id: int, project_id: int) -> bool:
    try:
        project = get_quotation_project_for_user(user_id, project_id)
        if project is None:
            return False
        db.session.delete(project)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        raise


def add_quotation_item_for_user(
    user_id: int,
    project_id: int,
    *,
    name: str,
    quantity: Decimal,
    unit: str,
) -> QuotationProject | None:
    try:
        project = get_quotation_project_for_user(user_id, project_id)
        if project is None:
            return None
        next_position = max((item.position for item in project.items), default=-1) + 1
        project.items.append(
            QuotationItem(
                name=name,
                quantity=quantity,
                unit=unit,
                position=next_position,
            )
        )
        db.session.commit()
        return get_quotation_project_for_user(user_id, project_id)
    except IntegrityError as error:
        db.session.rollback()
        raise QuotationConflictError(
            "That item already exists in this comparison."
        ) from error
    except Exception:
        db.session.rollback()
        raise


def update_quotation_item_for_user(
    user_id: int,
    project_id: int,
    item_id: int,
    *,
    name: str,
    quantity: Decimal,
    unit: str,
) -> QuotationProject | None:
    try:
        project = get_quotation_project_for_user(user_id, project_id)
        if project is None:
            return None
        item = next((item for item in project.items if item.id == item_id), None)
        if item is None:
            return None
        item.name = name
        item.quantity = quantity
        item.unit = unit
        db.session.commit()
        return get_quotation_project_for_user(user_id, project_id)
    except IntegrityError as error:
        db.session.rollback()
        raise QuotationConflictError(
            "That item already exists in this comparison."
        ) from error
    except Exception:
        db.session.rollback()
        raise


def delete_quotation_item_for_user(
    user_id: int,
    project_id: int,
    item_id: int,
) -> QuotationProject | None:
    try:
        project = get_quotation_project_for_user(user_id, project_id)
        if project is None:
            return None
        item = next((item for item in project.items if item.id == item_id), None)
        if item is None:
            return None
        db.session.delete(item)
        db.session.commit()
        return get_quotation_project_for_user(user_id, project_id)
    except Exception:
        db.session.rollback()
        raise


def _validated_price_items(
    project: QuotationProject,
    prices: dict[int, Decimal],
) -> dict[int, Decimal]:
    project_item_ids = {item.id for item in project.items}
    if not set(prices).issubset(project_item_ids):
        raise ValueError("A supplied price does not belong to this comparison.")
    return prices


def _replace_quote_prices(
    quotation: SupplierQuotation,
    prices: dict[int, Decimal],
) -> None:
    quotation.prices = [
        SupplierQuotationPrice(item_id=item_id, unit_price=unit_price)
        for item_id, unit_price in prices.items()
    ]


def add_supplier_quotation_for_user(
    user_id: int,
    project_id: int,
    *,
    supplier: str,
    contact: str | None,
    valid_until: date,
    delivery_cost: Decimal,
    discount: Decimal,
    tax_mode: str,
    tax_rate: Decimal,
    delivery_days: int | None,
    payment_terms: str | None,
    prices: dict[int, Decimal],
) -> QuotationProject | None:
    try:
        project = get_quotation_project_for_user(user_id, project_id)
        if project is None:
            return None
        prices = _validated_price_items(project, prices)
        quotation = SupplierQuotation(
            supplier=supplier,
            contact=contact,
            valid_until=valid_until,
            delivery_cost=delivery_cost,
            discount=discount,
            tax_mode=tax_mode,
            tax_rate=tax_rate,
            delivery_days=delivery_days,
            payment_terms=payment_terms,
        )
        _replace_quote_prices(quotation, prices)
        project.quotations.append(quotation)
        db.session.commit()
        return get_quotation_project_for_user(user_id, project_id)
    except IntegrityError as error:
        db.session.rollback()
        raise QuotationConflictError(
            "That supplier already has a quotation in this comparison."
        ) from error
    except Exception:
        db.session.rollback()
        raise


def update_supplier_quotation_for_user(
    user_id: int,
    project_id: int,
    quotation_id: int,
    **changes,
) -> QuotationProject | None:
    try:
        project = get_quotation_project_for_user(user_id, project_id)
        if project is None:
            return None
        quotation = next(
            (quote for quote in project.quotations if quote.id == quotation_id),
            None,
        )
        if quotation is None:
            return None
        prices = _validated_price_items(project, changes.pop("prices"))
        for field, value in changes.items():
            setattr(quotation, field, value)
        _replace_quote_prices(quotation, prices)
        db.session.commit()
        return get_quotation_project_for_user(user_id, project_id)
    except IntegrityError as error:
        db.session.rollback()
        raise QuotationConflictError(
            "That supplier already has a quotation in this comparison."
        ) from error
    except Exception:
        db.session.rollback()
        raise


def delete_supplier_quotation_for_user(
    user_id: int,
    project_id: int,
    quotation_id: int,
) -> QuotationProject | None:
    try:
        project = get_quotation_project_for_user(user_id, project_id)
        if project is None:
            return None
        quotation = next(
            (quote for quote in project.quotations if quote.id == quotation_id),
            None,
        )
        if quotation is None:
            return None
        was_preferred = quotation.preferred
        db.session.delete(quotation)
        if was_preferred:
            project.status = "comparing"
        db.session.commit()
        return get_quotation_project_for_user(user_id, project_id)
    except Exception:
        db.session.rollback()
        raise


def set_preferred_supplier_for_user(
    user_id: int,
    project_id: int,
    quotation_id: int,
    preferred: bool,
) -> QuotationProject | None:
    try:
        project = db.session.scalar(
            select(QuotationProject)
            .where(
                QuotationProject.id == project_id,
                QuotationProject.user_id == user_id,
            )
            .with_for_update()
        )
        if project is None:
            return None
        quotation = db.session.scalar(
            select(SupplierQuotation).where(
                SupplierQuotation.id == quotation_id,
                SupplierQuotation.project_id == project_id,
            )
        )
        if quotation is None:
            return None

        db.session.execute(
            update(SupplierQuotation)
            .where(SupplierQuotation.project_id == project_id)
            .values(preferred=False)
        )
        if preferred:
            quotation.preferred = True
            project.status = "supplier_selected"
        else:
            project.status = "comparing"
        db.session.commit()
        return get_quotation_project_for_user(user_id, project_id)
    except Exception:
        db.session.rollback()
        raise

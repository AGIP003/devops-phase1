from datetime import date
from decimal import Decimal, InvalidOperation
import re

from flask import Blueprint, abort, g, jsonify, request

from app.middleware import login_required
from app.serializers import quotation_project_to_dict
from app.services.quotation_service import (
    QuotationConflictError,
    add_quotation_item_for_user,
    add_supplier_quotation_for_user,
    create_quotation_project_for_user,
    delete_quotation_item_for_user,
    delete_quotation_project_for_user,
    delete_supplier_quotation_for_user,
    get_quotation_project_for_user,
    list_quotation_projects_for_user,
    set_preferred_supplier_for_user,
    update_quotation_item_for_user,
    update_quotation_item_prices_for_user,
    update_quotation_project_for_user,
    update_supplier_quotation_for_user,
)


quotation_bp = Blueprint(
    "quotations",
    __name__,
    url_prefix="/api/quotation-projects",
)

PROJECT_STATUSES = {"comparing", "supplier_selected", "archived"}
TAX_MODES = {"included", "excluded", "none"}


def _private_json(payload, status=200):
    response = jsonify(payload)
    response.headers["Cache-Control"] = "private, no-store"
    return response, status


def _payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, description="Payload must be an object")
    return data


def _text(data, key, *, maximum, required=True):
    value = data.get(key)
    if value is None and not required:
        return None
    if not isinstance(value, str):
        abort(400, description=f"{key} must be text")
    clean = " ".join(value.strip().split())
    if required and not clean:
        abort(400, description=f"{key} is required")
    if len(clean) > maximum:
        abort(400, description=f"{key} must be {maximum} characters or fewer")
    return clean or None


def _decimal(data, key, *, default=None, maximum=Decimal("9999999999.99")):
    raw_value = data.get(key, default)
    if raw_value is None:
        abort(400, description=f"{key} is required")
    try:
        value = Decimal(str(raw_value))
    except (InvalidOperation, TypeError, ValueError):
        abort(400, description=f"{key} must be a number")
    if not value.is_finite() or value < 0 or value > maximum:
        abort(400, description=f"{key} is outside the allowed range")
    if value.as_tuple().exponent < -2:
        abort(400, description=f"{key} can have at most two decimal places")
    return value


def _positive_decimal(data, key):
    value = _decimal(data, key)
    if value <= 0:
        abort(400, description=f"{key} must be greater than zero")
    return value


def _date(data, key, *, required=True):
    value = data.get(key)
    if value in (None, "") and not required:
        return None
    if not isinstance(value, str):
        abort(400, description=f"{key} must be a date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        abort(400, description=f"{key} must use YYYY-MM-DD")


def _optional_non_negative_integer(data, key):
    value = data.get(key)
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        abort(400, description=f"{key} must be a whole number")
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        abort(400, description=f"{key} must be a whole number")
    if parsed < 0 or str(parsed) != str(value).strip():
        abort(400, description=f"{key} must be a non-negative whole number")
    return parsed


def _prices(data):
    raw_prices = data.get("prices", [])
    if not isinstance(raw_prices, list):
        abort(400, description="prices must be a list")
    prices = {}
    for price in raw_prices:
        if not isinstance(price, dict):
            abort(400, description="Each price must be an object")
        item_id = price.get("itemId")
        if isinstance(item_id, bool):
            abort(400, description="itemId must be an integer")
        try:
            item_id = int(item_id)
        except (TypeError, ValueError):
            abort(400, description="itemId must be an integer")
        if item_id <= 0 or item_id in prices:
            abort(400, description="Each item may have one price")
        prices[item_id] = _decimal(price, "unitPrice")
    return prices


def _supplier_prices(data):
    raw_prices = data.get("prices")
    if not isinstance(raw_prices, list) or not raw_prices:
        abort(400, description="prices must be a non-empty list")

    prices = {}
    for price in raw_prices:
        if not isinstance(price, dict):
            abort(400, description="Each supplier price must be an object")

        quotation_id = price.get("quotationId")
        if isinstance(quotation_id, bool):
            abort(400, description="quotationId must be an integer")
        try:
            quotation_id = int(quotation_id)
        except (TypeError, ValueError):
            abort(400, description="quotationId must be an integer")
        if quotation_id <= 0 or quotation_id in prices:
            abort(400, description="Each supplier may have one price")

        unit_price = price.get("unitPrice")
        prices[quotation_id] = (
            None if unit_price in (None, "") else _decimal(price, "unitPrice")
        )

    return prices


def _project_fields(data):
    return {
        "title": _text(data, "title", maximum=100),
        "category": _text(data, "category", maximum=50),
        "notes": _text(data, "notes", maximum=300, required=False),
    }


def _quotation_fields(data):
    tax_mode = data.get("taxMode", "included")
    if tax_mode not in TAX_MODES:
        abort(400, description="taxMode must be included, excluded or none")
    tax_rate = _decimal(
        data,
        "taxRate",
        default="0",
        maximum=Decimal("100"),
    )
    if tax_mode != "excluded":
        tax_rate = Decimal("0")
    return {
        "supplier": _text(data, "supplier", maximum=100),
        "contact": _text(data, "contact", maximum=100, required=False),
        "valid_until": _date(data, "validUntil", required=False),
        "delivery_cost": _decimal(data, "deliveryCost", default="0"),
        "discount": _decimal(data, "discount", default="0"),
        "tax_mode": tax_mode,
        "tax_rate": tax_rate,
        "delivery_days": _optional_non_negative_integer(data, "deliveryDays"),
        "payment_terms": _text(
            data,
            "paymentTerms",
            maximum=150,
            required=False,
        ),
        "prices": _prices(data),
    }


@quotation_bp.get("")
@login_required
def list_projects():
    projects = list_quotation_projects_for_user(g.current_user["user_id"])
    return _private_json([quotation_project_to_dict(project) for project in projects])


@quotation_bp.post("")
@login_required
def create_project():
    data = _payload()
    fields = _project_fields(data)
    currency_code = str(data.get("currencyCode", "KES")).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", currency_code):
        abort(400, description="currencyCode must be a three-letter code")
    project = create_quotation_project_for_user(
        g.current_user["user_id"],
        **fields,
        currency_code=currency_code,
    )
    return _private_json({"data": quotation_project_to_dict(project)}, 201)


@quotation_bp.get("/<int:project_id>")
@login_required
def get_project(project_id):
    project = get_quotation_project_for_user(g.current_user["user_id"], project_id)
    if project is None:
        abort(404, description="Quotation comparison not found")
    return _private_json({"data": quotation_project_to_dict(project)})


@quotation_bp.patch("/<int:project_id>")
@login_required
def update_project(project_id):
    data = _payload()
    fields = _project_fields(data)
    status = data.get("status", "comparing")
    if status not in PROJECT_STATUSES:
        abort(400, description="Invalid quotation comparison status")
    project = update_quotation_project_for_user(
        g.current_user["user_id"],
        project_id,
        **fields,
        status=status,
    )
    if project is None:
        abort(404, description="Quotation comparison not found")
    return _private_json({"data": quotation_project_to_dict(project)})


@quotation_bp.delete("/<int:project_id>")
@login_required
def delete_project(project_id):
    if not delete_quotation_project_for_user(g.current_user["user_id"], project_id):
        abort(404, description="Quotation comparison not found")
    return _private_json({"status": "success"})


@quotation_bp.post("/<int:project_id>/items")
@login_required
def add_item(project_id):
    data = _payload()
    try:
        project = add_quotation_item_for_user(
            g.current_user["user_id"],
            project_id,
            name=_text(data, "name", maximum=100),
            quantity=_positive_decimal(data, "quantity"),
            unit=_text(data, "unit", maximum=30),
        )
    except QuotationConflictError as error:
        abort(409, description=str(error))
    if project is None:
        abort(404, description="Quotation comparison not found")
    return _private_json({"data": quotation_project_to_dict(project)}, 201)


@quotation_bp.patch("/<int:project_id>/items/<int:item_id>")
@login_required
def update_item(project_id, item_id):
    data = _payload()
    try:
        project = update_quotation_item_for_user(
            g.current_user["user_id"],
            project_id,
            item_id,
            name=_text(data, "name", maximum=100),
            quantity=_positive_decimal(data, "quantity"),
            unit=_text(data, "unit", maximum=30),
        )
    except QuotationConflictError as error:
        abort(409, description=str(error))
    if project is None:
        abort(404, description="Quotation item not found")
    return _private_json({"data": quotation_project_to_dict(project)})


@quotation_bp.delete("/<int:project_id>/items/<int:item_id>")
@login_required
def delete_item(project_id, item_id):
    project = delete_quotation_item_for_user(
        g.current_user["user_id"], project_id, item_id
    )
    if project is None:
        abort(404, description="Quotation item not found")
    return _private_json({"data": quotation_project_to_dict(project)})


@quotation_bp.patch("/<int:project_id>/items/<int:item_id>/prices")
@login_required
def update_item_prices(project_id, item_id):
    data = _payload()
    try:
        project = update_quotation_item_prices_for_user(
            g.current_user["user_id"],
            project_id,
            item_id,
            prices=_supplier_prices(data),
        )
    except ValueError as error:
        abort(400, description=str(error))
    if project is None:
        abort(404, description="Quotation item not found")
    return _private_json({"data": quotation_project_to_dict(project)})


@quotation_bp.post("/<int:project_id>/quotes")
@login_required
def add_quote(project_id):
    data = _payload()
    try:
        project = add_supplier_quotation_for_user(
            g.current_user["user_id"],
            project_id,
            **_quotation_fields(data),
        )
    except QuotationConflictError as error:
        abort(409, description=str(error))
    except ValueError as error:
        abort(400, description=str(error))
    if project is None:
        abort(404, description="Quotation comparison not found")
    return _private_json({"data": quotation_project_to_dict(project)}, 201)


@quotation_bp.patch("/<int:project_id>/quotes/<int:quotation_id>")
@login_required
def update_quote(project_id, quotation_id):
    data = _payload()
    try:
        project = update_supplier_quotation_for_user(
            g.current_user["user_id"],
            project_id,
            quotation_id,
            **_quotation_fields(data),
        )
    except QuotationConflictError as error:
        abort(409, description=str(error))
    except ValueError as error:
        abort(400, description=str(error))
    if project is None:
        abort(404, description="Supplier quotation not found")
    return _private_json({"data": quotation_project_to_dict(project)})


@quotation_bp.delete("/<int:project_id>/quotes/<int:quotation_id>")
@login_required
def delete_quote(project_id, quotation_id):
    project = delete_supplier_quotation_for_user(
        g.current_user["user_id"], project_id, quotation_id
    )
    if project is None:
        abort(404, description="Supplier quotation not found")
    return _private_json({"data": quotation_project_to_dict(project)})


@quotation_bp.patch("/<int:project_id>/quotes/<int:quotation_id>/preference")
@login_required
def set_preferred_quote(project_id, quotation_id):
    data = _payload()
    preferred = data.get("preferred")
    if not isinstance(preferred, bool):
        abort(400, description="preferred must be true or false")
    project = set_preferred_supplier_for_user(
        g.current_user["user_id"], project_id, quotation_id, preferred
    )
    if project is None:
        abort(404, description="Supplier quotation not found")
    return _private_json({"data": quotation_project_to_dict(project)})

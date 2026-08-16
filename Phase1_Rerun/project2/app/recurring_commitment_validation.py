from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.services.recurring_commitment_service import (
    CreateRecurringCommitmentInput,
    RecurringCommitmentValidationError,
    ResolveCommitmentCycleInput,
)


def _decimal_value(value, field: str, *, optional: bool = False) -> Decimal | None:
    if optional and (value is None or value == ""):
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise RecurringCommitmentValidationError(
            f"{field} must be a number"
        ) from error
    if not amount.is_finite():
        raise RecurringCommitmentValidationError(f"{field} must be finite")
    if amount.as_tuple().exponent < -2:
        raise RecurringCommitmentValidationError(
            f"{field} cannot have more than 2 decimal places"
        )
    return amount


def _date_value(value, field: str, *, default_today: bool = False) -> date:
    if default_today and not value:
        return date.today()
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError) as error:
        raise RecurringCommitmentValidationError(
            f"{field} must use YYYY-MM-DD"
        ) from error


def _optional_int(value, field: str) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise RecurringCommitmentValidationError(f"{field} must be a whole number")
    try:
        return int(str(value))
    except (TypeError, ValueError) as error:
        raise RecurringCommitmentValidationError(
            f"{field} must be a whole number"
        ) from error


def parse_recurring_commitment_create_payload(
    data: object,
) -> CreateRecurringCommitmentInput:
    if not isinstance(data, dict):
        raise RecurringCommitmentValidationError("Payload must be an object")

    auto_renews = data.get("autoRenews")
    if auto_renews is not None and not isinstance(auto_renews, bool):
        raise RecurringCommitmentValidationError("Auto-renew must be true or false")

    return CreateRecurringCommitmentInput(
        kind=str(data.get("kind", "")).strip().lower(),
        name=data.get("name", ""),
        provider=data.get("provider"),
        category=data.get("category"),
        amount=_decimal_value(data.get("amount"), "Amount") or Decimal("0"),
        amount_kind=str(data.get("amountKind", "fixed")).strip().lower(),
        currency_code=data.get("currencyCode", "KES"),
        next_due_date=_date_value(data.get("nextDueDate"), "Next due date"),
        frequency=str(data.get("frequency", "")).strip().lower(),
        custom_interval_days=_optional_int(
            data.get("customIntervalDays"),
            "Custom interval",
        ),
        auto_renews=auto_renews,
        notes=data.get("notes"),
        created_via="manual",
    )


def parse_commitment_cycle_payload(data: object) -> ResolveCommitmentCycleInput:
    if not isinstance(data, dict):
        raise RecurringCommitmentValidationError("Payload must be an object")
    return ResolveCommitmentCycleInput(
        resolution=str(data.get("resolution", "")).strip().lower(),
        actual_amount=_decimal_value(
            data.get("actualAmount"),
            "Paid amount",
            optional=True,
        ),
        resolved_on=_date_value(
            data.get("resolvedOn"),
            "Payment date",
            default_today=True,
        ),
        notes=data.get("notes"),
        created_via="manual",
    )


def parse_commitment_status_payload(data: object) -> str:
    if not isinstance(data, dict):
        raise RecurringCommitmentValidationError("Payload must be an object")
    return str(data.get("status", "")).strip().lower()

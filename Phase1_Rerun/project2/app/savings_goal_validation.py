from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.services.savings_goal_service import (
    CreateSavingsGoalEntryInput,
    CreateSavingsGoalInput,
    SavingsGoalValidationError,
)


def _decimal_value(value, field: str, *, optional: bool = False) -> Decimal | None:
    if optional and (value is None or value == ""):
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise SavingsGoalValidationError(f"{field} must be a number") from error
    if not amount.is_finite():
        raise SavingsGoalValidationError(f"{field} must be finite")
    if amount.as_tuple().exponent < -2:
        raise SavingsGoalValidationError(
            f"{field} cannot have more than 2 decimal places"
        )
    return amount


def _date_value(value, field: str, *, default_today: bool = False) -> date:
    if default_today and not value:
        return date.today()
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError) as error:
        raise SavingsGoalValidationError(f"{field} must use YYYY-MM-DD") from error


def parse_savings_goal_create_payload(data: object) -> CreateSavingsGoalInput:
    if not isinstance(data, dict):
        raise SavingsGoalValidationError("Payload must be an object")
    return CreateSavingsGoalInput(
        name=data.get("name", ""),
        target_amount=(
            _decimal_value(data.get("targetAmount"), "Target amount")
            or Decimal("0")
        ),
        target_date=_date_value(data.get("targetDate"), "Target date"),
        contribution_frequency=str(
            data.get("contributionFrequency", "")
        ).strip().lower(),
        current_savings=(
            _decimal_value(
                data.get("currentSavings", "0"),
                "Current savings",
            )
            or Decimal("0")
        ),
        currency_code=data.get("currencyCode", "KES"),
        notes=data.get("notes"),
        created_via="manual",
    )


def parse_savings_goal_entry_payload(
    data: object,
) -> CreateSavingsGoalEntryInput:
    if not isinstance(data, dict):
        raise SavingsGoalValidationError("Payload must be an object")
    return CreateSavingsGoalEntryInput(
        entry_type=str(data.get("entryType", "")).strip().lower(),
        amount=(
            _decimal_value(data.get("amount"), "Activity amount")
            or Decimal("0")
        ),
        occurred_on=_date_value(
            data.get("occurredOn"),
            "Activity date",
            default_today=True,
        ),
        notes=data.get("notes"),
        created_via="manual",
    )

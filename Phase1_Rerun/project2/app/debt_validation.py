from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.services.debt_service import (
    CreateDebtEntryInput,
    CreateDebtInput,
    DebtFeeTermInput,
    DebtScheduleInput,
    DebtValidationError,
)


def _decimal_value(value, field: str, *, optional: bool = False) -> Decimal | None:
    if optional and (value is None or value == ""):
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise DebtValidationError(f"{field} must be a number") from error
    if not amount.is_finite():
        raise DebtValidationError(f"{field} must be finite")
    if amount.as_tuple().exponent < -2:
        raise DebtValidationError(f"{field} cannot have more than 2 decimal places")
    return amount


def _interest_rate(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        rate = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise DebtValidationError("Interest rate must be a number") from error
    if not rate.is_finite() or rate <= 0:
        raise DebtValidationError("Interest rate must be positive")
    if rate.as_tuple().exponent < -4:
        raise DebtValidationError("Interest rate cannot have more than 4 decimal places")
    return rate


def _date_value(value, field: str, *, optional: bool = False) -> date | None:
    if optional and not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError) as error:
        raise DebtValidationError(f"{field} must use YYYY-MM-DD") from error


def _boolean_value(value, field: str, default: bool = False) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise DebtValidationError(f"{field} must be true or false")
    return value


def _integer_value(value, field: str, default: int = 1) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise DebtValidationError(f"{field} must be a whole number") from error


def parse_debt_create_payload(data: object) -> CreateDebtInput:
    if not isinstance(data, dict):
        raise DebtValidationError("Payload must be an object")

    schedule_data = data.get("schedule")
    schedule = None
    if schedule_data is not None:
        if not isinstance(schedule_data, dict):
            raise DebtValidationError("Schedule must be an object")
        schedule = DebtScheduleInput(
            frequency=str(schedule_data.get("frequency", "")).strip().lower(),
            interval_count=_integer_value(
                schedule_data.get("intervalCount"),
                "Schedule interval",
            ),
            installment_amount=_decimal_value(
                schedule_data.get("installmentAmount"),
                "Installment amount",
                optional=True,
            ),
            next_due_date=_date_value(
                schedule_data.get("nextDueDate"),
                "Next payment date",
            ),
            final_due_date=_date_value(
                schedule_data.get("finalDueDate"),
                "Final payoff date",
                optional=True,
            ),
        )

    fee_data = data.get("feeTerms", [])
    if not isinstance(fee_data, list):
        raise DebtValidationError("Fee types must be a list")
    fee_terms = []
    for item in fee_data:
        if not isinstance(item, dict):
            raise DebtValidationError("Each fee type must be an object")
        fee_terms.append(
            DebtFeeTermInput(
                fee_category=str(item.get("feeCategory", "")).strip().lower(),
                custom_fee_name=item.get("customFeeName"),
            )
        )

    has_interest = _boolean_value(data.get("hasInterest"), "Has interest")
    return CreateDebtInput(
        title=data.get("title", ""),
        direction=str(data.get("direction", "")).strip().lower(),
        category=str(data.get("category", "")).strip().lower(),
        tracking_kind=str(data.get("trackingKind", "")).strip().lower(),
        original_amount=_decimal_value(
            data.get("originalAmount"),
            "Original amount",
            optional=True,
        ),
        current_balance=_decimal_value(
            data.get("currentBalance"),
            "Current outstanding balance",
            optional=True,
        ),
        amount_repaid_before_tracking=(
            _decimal_value(
                data.get("amountAlreadyRepaid", "0"),
                "Amount already repaid",
            )
            or Decimal("0")
        ),
        counterparty=data.get("counterparty"),
        currency_code=data.get("currencyCode", "KES"),
        opened_on=_date_value(data.get("openedOn"), "Date opened", optional=True),
        notes=data.get("notes"),
        has_interest=has_interest,
        stated_interest_rate=_interest_rate(data.get("statedInterestRate")),
        interest_period=(
            str(data.get("interestPeriod", "")).strip().lower() or None
        ),
        schedule=schedule,
        fee_terms=tuple(fee_terms),
        created_via="manual",
    )


def parse_debt_entry_payload(data: object) -> CreateDebtEntryInput:
    if not isinstance(data, dict):
        raise DebtValidationError("Payload must be an object")

    return CreateDebtEntryInput(
        entry_type=str(data.get("entryType", "")).strip().lower(),
        amount=(
            _decimal_value(data.get("amount"), "Entry amount")
            or Decimal("0")
        ),
        occurred_on=_date_value(data.get("occurredOn"), "Entry date"),
        fee_category=(
            str(data.get("feeCategory", "")).strip().lower() or None
        ),
        custom_fee_name=data.get("customFeeName"),
        notes=data.get("notes"),
        create_transaction=_boolean_value(
            data.get("createTransaction"),
            "Create transaction",
        ),
        payment_method_name=(
            str(data.get("paymentMethod", "")).strip().lower() or None
        ),
        created_via="manual",
    )

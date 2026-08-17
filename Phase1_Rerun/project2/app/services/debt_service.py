from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.debt import Debt, DebtEntry, DebtFeeTerm, DebtSchedule
from app.services.transaction_service import build_transaction_for_user


DEBT_DIRECTIONS = {"i_owe", "owed_to_me"}
DEBT_CATEGORIES = {
    "personal",
    "mobile_loan",
    "bank",
    "sacco",
    "bnpl",
    "employer",
    "business",
    "other",
}
DEBT_SOURCES = {"manual", "telegram", "statement_import", "sms_import", "api"}
FEE_CATEGORIES = {
    "processing",
    "origination",
    "late_payment",
    "insurance",
    "service",
    "restructuring",
    "legal_collection",
    "other",
}
INTEREST_PERIODS = {"annual", "monthly", "fixed", "other"}
REPAYMENT_FREQUENCIES = {"one_time", "daily", "weekly", "monthly"}
ENTRY_TYPES = {
    "repayment",
    "interest",
    "fee",
    "adjustment_increase",
    "adjustment_decrease",
}


class DebtValidationError(ValueError):
    """Raised when a debt command violates a domain invariant."""


@dataclass(frozen=True, slots=True)
class DebtScheduleInput:
    frequency: str
    next_due_date: date
    installment_amount: Decimal | None = None
    final_due_date: date | None = None
    interval_count: int = 1


@dataclass(frozen=True, slots=True)
class DebtFeeTermInput:
    fee_category: str
    custom_fee_name: str | None = None


@dataclass(frozen=True, slots=True)
class CreateDebtInput:
    title: str
    direction: str
    category: str
    tracking_kind: str
    original_amount: Decimal | None = None
    current_balance: Decimal | None = None
    amount_repaid_before_tracking: Decimal = Decimal("0")
    counterparty: str | None = None
    currency_code: str = "KES"
    opened_on: date | None = None
    notes: str | None = None
    has_interest: bool = False
    stated_interest_rate: Decimal | None = None
    interest_period: str | None = None
    schedule: DebtScheduleInput | None = None
    fee_terms: tuple[DebtFeeTermInput, ...] = ()
    created_via: str = "manual"
    external_reference: str | None = None


@dataclass(frozen=True, slots=True)
class CreateDebtEntryInput:
    entry_type: str
    amount: Decimal
    occurred_on: date
    fee_category: str | None = None
    custom_fee_name: str | None = None
    notes: str | None = None
    create_transaction: bool = False
    payment_method_name: str | None = None
    created_via: str = "manual"
    external_reference: str | None = None


def _debt_select():
    return select(Debt).options(
        selectinload(Debt.schedule),
        selectinload(Debt.fee_terms),
        selectinload(Debt.entries).selectinload(DebtEntry.transaction),
    )


def _clean_text(value: str | None, field: str, maximum: int, required: bool = False):
    clean_value = str(value or "").strip()
    if required and not clean_value:
        raise DebtValidationError(f"{field} is required")
    if len(clean_value) > maximum:
        raise DebtValidationError(f"{field} cannot exceed {maximum} characters")
    return clean_value or None


def _validate_positive_amount(value: Decimal | None, field: str) -> Decimal:
    if value is None or not value.is_finite() or value <= 0:
        raise DebtValidationError(f"{field} must be a positive amount")
    return value.quantize(Decimal("0.01"))


def _validate_nonnegative_amount(value: Decimal, field: str) -> Decimal:
    if not value.is_finite() or value < 0:
        raise DebtValidationError(f"{field} cannot be negative")
    return value.quantize(Decimal("0.01"))


def _validate_schedule(schedule: DebtScheduleInput | None) -> DebtScheduleInput | None:
    if schedule is None:
        return None
    if schedule.frequency not in REPAYMENT_FREQUENCIES:
        raise DebtValidationError("Invalid repayment frequency")
    if schedule.interval_count < 1:
        raise DebtValidationError("Schedule interval must be at least 1")
    if schedule.installment_amount is not None:
        _validate_positive_amount(schedule.installment_amount, "Installment amount")
    if schedule.final_due_date and schedule.final_due_date < schedule.next_due_date:
        raise DebtValidationError("Final payoff date cannot be before the next payment date")
    return schedule


def _validate_fee_terms(
    fee_terms: tuple[DebtFeeTermInput, ...],
) -> tuple[DebtFeeTermInput, ...]:
    validated = []
    seen = set()
    for term in fee_terms:
        if term.fee_category not in FEE_CATEGORIES:
            raise DebtValidationError("Invalid fee type")
        custom_name = _clean_text(term.custom_fee_name, "Custom fee name", 100)
        if term.fee_category == "other" and not custom_name:
            raise DebtValidationError("A custom fee name is required for Other")
        normalized = (term.fee_category, custom_name.lower() if custom_name else None)
        if normalized in seen:
            raise DebtValidationError("Duplicate fee type")
        seen.add(normalized)
        validated.append(DebtFeeTermInput(term.fee_category, custom_name))
    return tuple(validated)


def _validate_create_input(data: CreateDebtInput) -> tuple[CreateDebtInput, Decimal]:
    title = _clean_text(data.title, "Debt description", 140, required=True)
    counterparty = _clean_text(data.counterparty, "Counterparty", 100)
    notes = _clean_text(data.notes, "Notes", 1000)

    if data.direction not in DEBT_DIRECTIONS:
        raise DebtValidationError("Invalid debt direction")
    if data.category not in DEBT_CATEGORIES:
        raise DebtValidationError("Invalid debt category")
    if data.tracking_kind not in {"new", "existing"}:
        raise DebtValidationError("Debt must be new or existing")
    if data.created_via not in DEBT_SOURCES:
        raise DebtValidationError("Invalid debt source")

    currency_code = str(data.currency_code or "").strip().upper()
    if len(currency_code) != 3 or not currency_code.isalpha():
        raise DebtValidationError("Currency code must contain three letters")

    prior_repayment = _validate_nonnegative_amount(
        data.amount_repaid_before_tracking,
        "Amount already repaid",
    )
    original_amount = None
    if data.original_amount is not None:
        original_amount = _validate_positive_amount(data.original_amount, "Original amount")

    if data.tracking_kind == "new":
        if original_amount is None:
            raise DebtValidationError("Original amount is required for a new debt")
        if prior_repayment > original_amount:
            raise DebtValidationError("Amount already repaid cannot exceed the original amount")
        opening_balance = original_amount - prior_repayment
    else:
        opening_balance = _validate_positive_amount(
            data.current_balance,
            "Current outstanding balance",
        )

    interest_rate = data.stated_interest_rate
    if interest_rate is not None:
        if not interest_rate.is_finite() or interest_rate <= 0:
            raise DebtValidationError("Interest rate must be positive")
        interest_rate = interest_rate.quantize(Decimal("0.0001"))
        if not data.has_interest:
            raise DebtValidationError("Enable interest before entering a rate")
    if data.interest_period and data.interest_period not in INTEREST_PERIODS:
        raise DebtValidationError("Invalid interest period")

    schedule = _validate_schedule(data.schedule)
    fee_terms = _validate_fee_terms(data.fee_terms)
    external_reference = _clean_text(
        data.external_reference,
        "External reference",
        160,
    )

    return CreateDebtInput(
        title=title or "",
        direction=data.direction,
        category=data.category,
        tracking_kind=data.tracking_kind,
        original_amount=original_amount,
        current_balance=data.current_balance,
        amount_repaid_before_tracking=prior_repayment,
        counterparty=counterparty,
        currency_code=currency_code,
        opened_on=data.opened_on,
        notes=notes,
        has_interest=data.has_interest,
        stated_interest_rate=interest_rate,
        interest_period=data.interest_period if data.has_interest else None,
        schedule=schedule,
        fee_terms=fee_terms,
        created_via=data.created_via,
        external_reference=external_reference,
    ), opening_balance


def get_debt_for_user(
    user_id: int,
    debt_id: int,
    *,
    for_update: bool = False,
) -> Debt | None:
    statement = _debt_select().where(
        Debt.id == debt_id,
        Debt.user_id == user_id,
        Debt.deleted_at.is_(None),
    )
    if for_update:
        statement = statement.with_for_update()
    return db.session.scalar(statement)


def list_debts_for_user(user_id: int) -> list[Debt]:
    statement = (
        _debt_select()
        .where(
            Debt.user_id == user_id,
            Debt.deleted_at.is_(None),
        )
        .order_by(Debt.created_at.desc(), Debt.id.desc())
    )
    return list(db.session.scalars(statement).unique().all())


def create_debt_for_user(user_id: int, data: CreateDebtInput) -> Debt:
    validated, opening_balance = _validate_create_input(data)

    if validated.external_reference:
        existing = db.session.scalar(
            _debt_select().where(
                Debt.user_id == user_id,
                Debt.created_via == validated.created_via,
                Debt.external_reference == validated.external_reference,
            )
        )
        if existing is not None:
            return existing

    try:
        debt = Debt(
            user_id=user_id,
            title=validated.title,
            direction=validated.direction,
            category=validated.category,
            counterparty=validated.counterparty,
            currency_code=validated.currency_code,
            tracking_kind=validated.tracking_kind,
            original_amount=validated.original_amount,
            opening_balance=opening_balance,
            amount_repaid_before_tracking=validated.amount_repaid_before_tracking,
            opened_on=validated.opened_on,
            notes=validated.notes,
            has_interest=validated.has_interest,
            stated_interest_rate=validated.stated_interest_rate,
            interest_period=validated.interest_period,
            status="settled" if opening_balance == 0 else "active",
            created_via=validated.created_via,
            external_reference=validated.external_reference,
            schedule=(
                DebtSchedule(
                    frequency=validated.schedule.frequency,
                    interval_count=validated.schedule.interval_count,
                    installment_amount=validated.schedule.installment_amount,
                    next_due_date=validated.schedule.next_due_date,
                    final_due_date=validated.schedule.final_due_date,
                )
                if validated.schedule
                else None
            ),
            fee_terms=[
                DebtFeeTerm(
                    fee_category=term.fee_category,
                    custom_fee_name=term.custom_fee_name,
                )
                for term in validated.fee_terms
            ],
        )
        db.session.add(debt)
        db.session.commit()

        saved_debt = get_debt_for_user(user_id, debt.id)
        if saved_debt is None:
            raise RuntimeError("Created debt could not be reloaded")
        return saved_debt
    except IntegrityError:
        db.session.rollback()
        if validated.external_reference:
            existing = db.session.scalar(
                _debt_select().where(
                    Debt.user_id == user_id,
                    Debt.created_via == validated.created_via,
                    Debt.external_reference == validated.external_reference,
                )
            )
            if existing is not None:
                return existing
        raise
    except Exception:
        db.session.rollback()
        raise


def _validate_entry_input(data: CreateDebtEntryInput) -> CreateDebtEntryInput:
    if data.entry_type not in ENTRY_TYPES:
        raise DebtValidationError("Invalid debt entry type")
    amount = _validate_positive_amount(data.amount, "Entry amount")
    notes = _clean_text(data.notes, "Notes", 500)
    fee_category = data.fee_category
    custom_fee_name = _clean_text(data.custom_fee_name, "Custom fee name", 100)

    if data.entry_type == "fee":
        if fee_category not in FEE_CATEGORIES:
            raise DebtValidationError("A valid fee type is required")
        if fee_category == "other" and not custom_fee_name:
            raise DebtValidationError("A custom fee name is required for Other")
    else:
        fee_category = None
        custom_fee_name = None

    if data.create_transaction and data.entry_type != "repayment":
        raise DebtValidationError("Only repayments can create a transaction")
    if data.create_transaction and not data.payment_method_name:
        raise DebtValidationError("Payment method is required for a linked transaction")
    if data.created_via not in DEBT_SOURCES:
        raise DebtValidationError("Invalid debt source")

    return CreateDebtEntryInput(
        entry_type=data.entry_type,
        amount=amount,
        occurred_on=data.occurred_on,
        fee_category=fee_category,
        custom_fee_name=custom_fee_name,
        notes=notes,
        create_transaction=data.create_transaction,
        payment_method_name=data.payment_method_name,
        created_via=data.created_via,
        external_reference=_clean_text(
            data.external_reference,
            "External reference",
            160,
        ),
    )


def add_debt_entry_for_user(
    user_id: int,
    debt_id: int,
    data: CreateDebtEntryInput,
) -> Debt | None:
    validated = _validate_entry_input(data)
    debt = get_debt_for_user(user_id, debt_id)
    if debt is None:
        return None

    if validated.external_reference:
        existing_entry = db.session.scalar(
            select(DebtEntry).where(
                DebtEntry.debt_id == debt_id,
                DebtEntry.created_via == validated.created_via,
                DebtEntry.external_reference == validated.external_reference,
            )
        )
        if existing_entry is not None:
            return debt

    if (
        validated.entry_type in {"repayment", "adjustment_decrease"}
        and validated.amount > debt.current_balance
    ):
        raise DebtValidationError("Entry amount cannot exceed the outstanding balance")

    try:
        transaction = None
        if validated.create_transaction:
            transaction_type = "expense" if debt.direction == "i_owe" else "income"
            category_name = "loan" if debt.direction == "i_owe" else "debts paid"
            transaction = build_transaction_for_user(
                user_id=user_id,
                category_name=category_name,
                transaction_type=transaction_type,
                payment_method_name=validated.payment_method_name or "",
                amount=validated.amount,
                transaction_date=validated.occurred_on,
                description=f"Debt repayment: {debt.title}",
            )
            db.session.flush()

        entry = DebtEntry(
            debt=debt,
            entry_type=validated.entry_type,
            amount=validated.amount,
            occurred_on=validated.occurred_on,
            fee_category=validated.fee_category,
            custom_fee_name=validated.custom_fee_name,
            notes=validated.notes,
            transaction=transaction,
            created_via=validated.created_via,
            external_reference=validated.external_reference,
        )
        db.session.add(entry)
        db.session.flush()

        if debt.status not in {"written_off", "cancelled"}:
            debt.status = "settled" if debt.current_balance == 0 else "active"

        db.session.commit()
        return get_debt_for_user(user_id, debt_id)
    except Exception:
        db.session.rollback()
        raise


def _raw_debt_balance(
    debt: Debt,
    *,
    replacing_entry_id: int | None = None,
    replacement_type: str | None = None,
    replacement_amount: Decimal | None = None,
) -> Decimal:
    balance = Decimal(debt.opening_balance)
    for entry in debt.entries:
        if entry.id == replacing_entry_id:
            continue
        amount = Decimal(entry.amount)
        if entry.entry_type in {"interest", "fee", "adjustment_increase"}:
            balance += amount
        else:
            balance -= amount

    if replacement_type and replacement_amount is not None:
        if replacement_type in {"interest", "fee", "adjustment_increase"}:
            balance += replacement_amount
        else:
            balance -= replacement_amount
    return balance


def update_debt_for_user(
    user_id: int,
    debt_id: int,
    data: CreateDebtInput,
) -> Debt | None:
    """Update the debt plan while preserving all recorded activity rows."""
    validated, opening_balance = _validate_create_input(data)

    try:
        debt = get_debt_for_user(user_id, debt_id, for_update=True)
        if debt is None:
            db.session.rollback()
            return None

        debt.title = validated.title
        debt.direction = validated.direction
        debt.category = validated.category
        debt.counterparty = validated.counterparty
        debt.currency_code = validated.currency_code
        debt.tracking_kind = validated.tracking_kind
        debt.original_amount = validated.original_amount
        debt.opening_balance = opening_balance
        debt.amount_repaid_before_tracking = validated.amount_repaid_before_tracking
        debt.opened_on = validated.opened_on
        debt.notes = validated.notes
        debt.has_interest = validated.has_interest
        debt.stated_interest_rate = validated.stated_interest_rate
        debt.interest_period = validated.interest_period

        if _raw_debt_balance(debt) < 0:
            raise DebtValidationError(
                "The corrected opening amount cannot be lower than recorded repayments"
            )

        if validated.schedule is None:
            debt.schedule = None
        elif debt.schedule is None:
            debt.schedule = DebtSchedule(
                frequency=validated.schedule.frequency,
                interval_count=validated.schedule.interval_count,
                installment_amount=validated.schedule.installment_amount,
                next_due_date=validated.schedule.next_due_date,
                final_due_date=validated.schedule.final_due_date,
            )
        else:
            debt.schedule.frequency = validated.schedule.frequency
            debt.schedule.interval_count = validated.schedule.interval_count
            debt.schedule.installment_amount = validated.schedule.installment_amount
            debt.schedule.next_due_date = validated.schedule.next_due_date
            debt.schedule.final_due_date = validated.schedule.final_due_date

        debt.fee_terms.clear()
        db.session.flush()
        debt.fee_terms.extend(
            DebtFeeTerm(
                fee_category=term.fee_category,
                custom_fee_name=term.custom_fee_name,
            )
            for term in validated.fee_terms
        )

        for entry in debt.entries:
            if entry.transaction is not None:
                entry.transaction.description = f"Debt repayment: {debt.title}"

        if debt.status not in {"written_off", "cancelled"}:
            debt.status = "settled" if _raw_debt_balance(debt) == 0 else "active"

        db.session.commit()
        return get_debt_for_user(user_id, debt_id)
    except Exception:
        db.session.rollback()
        raise


def update_debt_entry_for_user(
    user_id: int,
    debt_id: int,
    entry_id: int,
    data: CreateDebtEntryInput,
) -> Debt | None:
    """Correct one debt activity and its linked transaction as one ACID unit."""
    validated = _validate_entry_input(data)

    try:
        debt = get_debt_for_user(user_id, debt_id, for_update=True)
        if debt is None:
            db.session.rollback()
            return None

        entry = next((item for item in debt.entries if item.id == entry_id), None)
        if entry is None:
            db.session.rollback()
            return None
        if entry.transaction is not None and validated.entry_type != "repayment":
            raise DebtValidationError(
                "A linked repayment must remain a repayment"
            )
        if _raw_debt_balance(
            debt,
            replacing_entry_id=entry_id,
            replacement_type=validated.entry_type,
            replacement_amount=validated.amount,
        ) < 0:
            raise DebtValidationError(
                "This correction would make the outstanding balance negative"
            )

        entry.entry_type = validated.entry_type
        entry.amount = validated.amount
        entry.occurred_on = validated.occurred_on
        entry.fee_category = validated.fee_category
        entry.custom_fee_name = validated.custom_fee_name
        entry.notes = validated.notes

        if entry.transaction is not None:
            if entry.transaction.user_id != user_id:
                raise RuntimeError("Linked transaction ownership is inconsistent")
            entry.transaction.amount = validated.amount
            entry.transaction.date = validated.occurred_on
            entry.transaction.description = f"Debt repayment: {debt.title}"

        if debt.status not in {"written_off", "cancelled"}:
            debt.status = "settled" if _raw_debt_balance(debt) == 0 else "active"

        db.session.commit()
        return get_debt_for_user(user_id, debt_id)
    except Exception:
        db.session.rollback()
        raise


def archive_debt_for_user(user_id: int, debt_id: int) -> bool:
    try:
        debt = get_debt_for_user(user_id, debt_id)
        if debt is None:
            return False
        debt.soft_delete()
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        raise

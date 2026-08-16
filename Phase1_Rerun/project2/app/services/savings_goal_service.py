from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_CEILING
from math import ceil

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.savings_goal import SavingsGoal, SavingsGoalEntry


GOAL_FREQUENCIES = {"weekly", "fortnightly", "monthly"}
GOAL_ENTRY_TYPES = {"contribution", "withdrawal"}
GOAL_SOURCES = {"manual", "telegram", "statement_import", "sms_import", "api"}


class SavingsGoalValidationError(ValueError):
    """Raised when a savings-goal command violates a domain rule."""


@dataclass(frozen=True, slots=True)
class CreateSavingsGoalInput:
    name: str
    target_amount: Decimal
    target_date: date
    contribution_frequency: str
    current_savings: Decimal = Decimal("0")
    currency_code: str = "KES"
    notes: str | None = None
    created_via: str = "manual"
    external_reference: str | None = None


@dataclass(frozen=True, slots=True)
class CreateSavingsGoalEntryInput:
    entry_type: str
    amount: Decimal
    occurred_on: date
    notes: str | None = None
    created_via: str = "manual"
    external_reference: str | None = None


@dataclass(frozen=True, slots=True)
class SavingsGoalPlan:
    remaining_amount: Decimal
    remaining_periods: int
    suggested_contribution: Decimal
    overdue: bool
    target_reached: bool


def _goal_select():
    return select(SavingsGoal).options(selectinload(SavingsGoal.entries))


def _clean_text(
    value: str | None,
    field: str,
    maximum: int,
    *,
    required: bool = False,
) -> str | None:
    clean_value = str(value or "").strip()
    if required and not clean_value:
        raise SavingsGoalValidationError(f"{field} is required")
    if len(clean_value) > maximum:
        raise SavingsGoalValidationError(
            f"{field} cannot exceed {maximum} characters"
        )
    return clean_value or None


def _money(value: Decimal, field: str, *, allow_zero: bool = False) -> Decimal:
    minimum_is_valid = value >= 0 if allow_zero else value > 0
    if not value.is_finite() or not minimum_is_valid:
        qualifier = "zero or a positive amount" if allow_zero else "a positive amount"
        raise SavingsGoalValidationError(f"{field} must be {qualifier}")
    return value.quantize(Decimal("0.01"))


def _validate_source(source: str) -> str:
    normalized = str(source or "").strip().lower()
    if normalized not in GOAL_SOURCES:
        raise SavingsGoalValidationError("Invalid goal source")
    return normalized


def _validate_create(data: CreateSavingsGoalInput) -> CreateSavingsGoalInput:
    name = _clean_text(data.name, "Goal name", 120, required=True) or ""
    notes = _clean_text(data.notes, "Notes", 1000)
    target_amount = _money(data.target_amount, "Target amount")
    current_savings = _money(
        data.current_savings,
        "Current savings",
        allow_zero=True,
    )
    frequency = str(data.contribution_frequency or "").strip().lower()
    if frequency not in GOAL_FREQUENCIES:
        raise SavingsGoalValidationError("Invalid saving frequency")
    if data.target_date < date.today():
        raise SavingsGoalValidationError("Target date cannot be in the past")

    currency_code = str(data.currency_code or "").strip().upper()
    if len(currency_code) != 3 or not currency_code.isalpha():
        raise SavingsGoalValidationError("Currency code must contain three letters")

    return CreateSavingsGoalInput(
        name=name,
        target_amount=target_amount,
        target_date=data.target_date,
        contribution_frequency=frequency,
        current_savings=current_savings,
        currency_code=currency_code,
        notes=notes,
        created_via=_validate_source(data.created_via),
        external_reference=_clean_text(
            data.external_reference,
            "External reference",
            160,
        ),
    )


def _validate_entry(
    data: CreateSavingsGoalEntryInput,
) -> CreateSavingsGoalEntryInput:
    entry_type = str(data.entry_type or "").strip().lower()
    if entry_type not in GOAL_ENTRY_TYPES:
        raise SavingsGoalValidationError("Activity must be money added or removed")
    return CreateSavingsGoalEntryInput(
        entry_type=entry_type,
        amount=_money(data.amount, "Activity amount"),
        occurred_on=data.occurred_on,
        notes=_clean_text(data.notes, "Notes", 500),
        created_via=_validate_source(data.created_via),
        external_reference=_clean_text(
            data.external_reference,
            "External reference",
            160,
        ),
    )


def _calendar_months_remaining(start: date, end: date) -> int:
    whole_months = (end.year - start.year) * 12 + end.month - start.month
    if end.day > start.day:
        whole_months += 1
    return max(1, whole_months)


def calculate_savings_goal_plan(
    goal: SavingsGoal,
    *,
    as_of: date | None = None,
) -> SavingsGoalPlan:
    today = as_of or date.today()
    current_savings = goal.current_savings
    remaining = max(Decimal(goal.target_amount) - current_savings, Decimal("0"))
    overdue = goal.target_date < today and remaining > 0

    if remaining == 0:
        periods = 0
        suggested = Decimal("0.00")
    else:
        days_remaining = max((goal.target_date - today).days, 0)
        if goal.contribution_frequency == "weekly":
            periods = max(1, ceil(days_remaining / 7))
        elif goal.contribution_frequency == "fortnightly":
            periods = max(1, ceil(days_remaining / 14))
        else:
            periods = _calendar_months_remaining(today, goal.target_date)
        suggested = (remaining / periods).quantize(
            Decimal("0.01"),
            rounding=ROUND_CEILING,
        )

    return SavingsGoalPlan(
        remaining_amount=remaining.quantize(Decimal("0.01")),
        remaining_periods=periods,
        suggested_contribution=suggested,
        overdue=overdue,
        target_reached=remaining == 0,
    )


def list_savings_goals_for_user(user_id: int) -> list[SavingsGoal]:
    statement = (
        _goal_select()
        .where(
            SavingsGoal.user_id == user_id,
            SavingsGoal.deleted_at.is_(None),
        )
        .order_by(SavingsGoal.target_date, SavingsGoal.id)
    )
    return list(db.session.scalars(statement).all())


def get_savings_goal_for_user(
    user_id: int,
    goal_id: int,
    *,
    for_update: bool = False,
) -> SavingsGoal | None:
    statement = _goal_select().where(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == user_id,
        SavingsGoal.deleted_at.is_(None),
    )
    if for_update:
        statement = statement.with_for_update()
    return db.session.scalar(statement)


def create_savings_goal_for_user(
    user_id: int,
    data: CreateSavingsGoalInput,
) -> SavingsGoal:
    validated = _validate_create(data)

    if validated.external_reference:
        existing = db.session.scalar(
            _goal_select().where(
                SavingsGoal.user_id == user_id,
                SavingsGoal.created_via == validated.created_via,
                SavingsGoal.external_reference == validated.external_reference,
            )
        )
        if existing is not None:
            return existing

    try:
        goal = SavingsGoal(
            user_id=user_id,
            name=validated.name,
            target_amount=validated.target_amount,
            target_date=validated.target_date,
            contribution_frequency=validated.contribution_frequency,
            currency_code=validated.currency_code,
            notes=validated.notes,
            created_via=validated.created_via,
            external_reference=validated.external_reference,
        )
        db.session.add(goal)

        if validated.current_savings > 0:
            goal.entries.append(
                SavingsGoalEntry(
                    entry_type="contribution",
                    amount=validated.current_savings,
                    occurred_on=date.today(),
                    notes="Opening savings",
                    created_via=validated.created_via,
                )
            )

        db.session.commit()
        return get_savings_goal_for_user(user_id, goal.id) or goal
    except IntegrityError as error:
        db.session.rollback()
        if validated.external_reference:
            existing = db.session.scalar(
                _goal_select().where(
                    SavingsGoal.user_id == user_id,
                    SavingsGoal.created_via == validated.created_via,
                    SavingsGoal.external_reference == validated.external_reference,
                )
            )
            if existing is not None:
                return existing
        raise error
    except Exception:
        db.session.rollback()
        raise


def add_savings_goal_entry_for_user(
    user_id: int,
    goal_id: int,
    data: CreateSavingsGoalEntryInput,
) -> SavingsGoal | None:
    validated = _validate_entry(data)

    try:
        goal = get_savings_goal_for_user(user_id, goal_id, for_update=True)
        if goal is None:
            db.session.rollback()
            return None

        if validated.external_reference:
            existing_entry = db.session.scalar(
                select(SavingsGoalEntry).where(
                    SavingsGoalEntry.goal_id == goal_id,
                    SavingsGoalEntry.created_via == validated.created_via,
                    SavingsGoalEntry.external_reference == validated.external_reference,
                )
            )
            if existing_entry is not None:
                db.session.rollback()
                return get_savings_goal_for_user(user_id, goal_id)

        if (
            validated.entry_type == "withdrawal"
            and validated.amount > goal.current_savings
        ):
            raise SavingsGoalValidationError(
                "Money removed cannot exceed the current savings"
            )

        goal.entries.append(
            SavingsGoalEntry(
                entry_type=validated.entry_type,
                amount=validated.amount,
                occurred_on=validated.occurred_on,
                notes=validated.notes,
                created_via=validated.created_via,
                external_reference=validated.external_reference,
            )
        )
        db.session.commit()
        return get_savings_goal_for_user(user_id, goal_id)
    except IntegrityError as error:
        db.session.rollback()
        if validated.external_reference:
            existing_entry = db.session.scalar(
                select(SavingsGoalEntry).where(
                    SavingsGoalEntry.goal_id == goal_id,
                    SavingsGoalEntry.created_via == validated.created_via,
                    SavingsGoalEntry.external_reference == validated.external_reference,
                )
            )
            if existing_entry is not None:
                return get_savings_goal_for_user(user_id, goal_id)
        raise error
    except Exception:
        db.session.rollback()
        raise


def archive_savings_goal_for_user(user_id: int, goal_id: int) -> bool:
    try:
        goal = get_savings_goal_for_user(user_id, goal_id)
        if goal is None:
            return False
        goal.soft_delete()
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        raise

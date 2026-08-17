from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.recurring_commitment import (
    CommitmentOccurrence,
    RecurringCommitment,
)


COMMITMENT_KINDS = {"bill", "subscription"}
AMOUNT_KINDS = {"fixed", "estimated"}
COMMITMENT_FREQUENCIES = {
    "weekly",
    "monthly",
    "quarterly",
    "termly",
    "yearly",
    "custom",
}
COMMITMENT_RESOLUTIONS = {"paid", "skipped"}
COMMITMENT_SOURCES = {"manual", "telegram", "statement_import", "sms_import", "api"}


class RecurringCommitmentValidationError(ValueError):
    """Raised when a recurring-commitment command breaks a domain rule."""


@dataclass(frozen=True, slots=True)
class CreateRecurringCommitmentInput:
    kind: str
    name: str
    amount: Decimal
    next_due_date: date
    frequency: str
    provider: str | None = None
    category: str | None = None
    amount_kind: str = "fixed"
    currency_code: str = "KES"
    custom_interval_days: int | None = None
    auto_renews: bool | None = None
    notes: str | None = None
    created_via: str = "manual"
    external_reference: str | None = None


@dataclass(frozen=True, slots=True)
class ResolveCommitmentCycleInput:
    resolution: str
    resolved_on: date
    actual_amount: Decimal | None = None
    notes: str | None = None
    created_via: str = "manual"
    external_reference: str | None = None


def _commitment_select():
    return select(RecurringCommitment).options(
        selectinload(RecurringCommitment.occurrences)
    )


def _clean_text(
    value: str | None,
    field: str,
    maximum: int,
    *,
    required: bool = False,
) -> str | None:
    clean_value = str(value or "").strip()
    if required and not clean_value:
        raise RecurringCommitmentValidationError(f"{field} is required")
    if len(clean_value) > maximum:
        raise RecurringCommitmentValidationError(
            f"{field} cannot exceed {maximum} characters"
        )
    return clean_value or None


def _money(value: Decimal, field: str) -> Decimal:
    if not value.is_finite() or value <= 0:
        raise RecurringCommitmentValidationError(f"{field} must be a positive amount")
    return value.quantize(Decimal("0.01"))


def _validate_source(source: str) -> str:
    normalized = str(source or "").strip().lower()
    if normalized not in COMMITMENT_SOURCES:
        raise RecurringCommitmentValidationError("Invalid commitment source")
    return normalized


def _validate_create(
    data: CreateRecurringCommitmentInput,
) -> CreateRecurringCommitmentInput:
    kind = str(data.kind or "").strip().lower()
    if kind not in COMMITMENT_KINDS:
        raise RecurringCommitmentValidationError("Type must be a bill or subscription")

    frequency = str(data.frequency or "").strip().lower()
    if frequency not in COMMITMENT_FREQUENCIES:
        raise RecurringCommitmentValidationError("Invalid payment frequency")

    amount_kind = str(data.amount_kind or "").strip().lower()
    if amount_kind not in AMOUNT_KINDS:
        raise RecurringCommitmentValidationError("Amount must be fixed or estimated")
    if kind == "subscription" and amount_kind != "fixed":
        raise RecurringCommitmentValidationError(
            "Subscription amounts must be recorded as fixed"
        )

    custom_interval_days = data.custom_interval_days
    if frequency == "custom":
        if custom_interval_days is None or not 1 <= custom_interval_days <= 366:
            raise RecurringCommitmentValidationError(
                "Custom frequency must be between 1 and 366 days"
            )
    else:
        custom_interval_days = None

    if kind == "subscription":
        if not isinstance(data.auto_renews, bool):
            raise RecurringCommitmentValidationError(
                "Choose whether the subscription renews automatically"
            )
        auto_renews = data.auto_renews
    else:
        auto_renews = None

    currency_code = str(data.currency_code or "").strip().upper()
    if len(currency_code) != 3 or not currency_code.isalpha():
        raise RecurringCommitmentValidationError(
            "Currency code must contain three letters"
        )

    return CreateRecurringCommitmentInput(
        kind=kind,
        name=_clean_text(data.name, "Name", 120, required=True) or "",
        amount=_money(data.amount, "Amount"),
        next_due_date=data.next_due_date,
        frequency=frequency,
        provider=_clean_text(data.provider, "Provider", 120),
        category=_clean_text(data.category, "Category", 80),
        amount_kind=amount_kind,
        currency_code=currency_code,
        custom_interval_days=custom_interval_days,
        auto_renews=auto_renews,
        notes=_clean_text(data.notes, "Notes", 1000),
        created_via=_validate_source(data.created_via),
        external_reference=_clean_text(
            data.external_reference,
            "External reference",
            160,
        ),
    )


def _validate_resolution(
    data: ResolveCommitmentCycleInput,
) -> ResolveCommitmentCycleInput:
    resolution = str(data.resolution or "").strip().lower()
    if resolution not in COMMITMENT_RESOLUTIONS:
        raise RecurringCommitmentValidationError("Cycle must be paid or skipped")

    actual_amount = data.actual_amount
    if resolution == "paid":
        if actual_amount is None:
            raise RecurringCommitmentValidationError("Paid amount is required")
        actual_amount = _money(actual_amount, "Paid amount")
    else:
        actual_amount = None

    return ResolveCommitmentCycleInput(
        resolution=resolution,
        resolved_on=data.resolved_on,
        actual_amount=actual_amount,
        notes=_clean_text(data.notes, "Notes", 500),
        created_via=_validate_source(data.created_via),
        external_reference=_clean_text(
            data.external_reference,
            "External reference",
            160,
        ),
    )


def _add_calendar_months(current: date, months: int, anchor_day: int) -> date:
    """Advance a calendar recurrence without letting month-end dates drift."""
    month_index = current.year * 12 + current.month - 1 + months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    day = min(anchor_day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def calculate_next_due_date(commitment: RecurringCommitment) -> date:
    if commitment.frequency == "weekly":
        return commitment.next_due_date + timedelta(days=7)
    if commitment.frequency == "custom":
        return commitment.next_due_date + timedelta(
            days=commitment.custom_interval_days or 1
        )

    months_by_frequency = {
        "monthly": 1,
        "quarterly": 3,
        "termly": 4,
        "yearly": 12,
    }
    return _add_calendar_months(
        commitment.next_due_date,
        months_by_frequency[commitment.frequency],
        commitment.recurrence_anchor_day,
    )


def list_recurring_commitments_for_user(
    user_id: int,
) -> list[RecurringCommitment]:
    statement = (
        _commitment_select()
        .where(
            RecurringCommitment.user_id == user_id,
            RecurringCommitment.deleted_at.is_(None),
        )
        .order_by(
            RecurringCommitment.status,
            RecurringCommitment.next_due_date,
            RecurringCommitment.id,
        )
    )
    return list(db.session.scalars(statement).all())


def get_recurring_commitment_for_user(
    user_id: int,
    commitment_id: int,
    *,
    for_update: bool = False,
) -> RecurringCommitment | None:
    statement = _commitment_select().where(
        RecurringCommitment.id == commitment_id,
        RecurringCommitment.user_id == user_id,
        RecurringCommitment.deleted_at.is_(None),
    )
    if for_update:
        statement = statement.with_for_update()
    return db.session.scalar(statement)


def create_recurring_commitment_for_user(
    user_id: int,
    data: CreateRecurringCommitmentInput,
) -> RecurringCommitment:
    validated = _validate_create(data)

    if validated.external_reference:
        existing = db.session.scalar(
            _commitment_select().where(
                RecurringCommitment.user_id == user_id,
                RecurringCommitment.created_via == validated.created_via,
                RecurringCommitment.external_reference
                == validated.external_reference,
            )
        )
        if existing is not None:
            return existing

    try:
        commitment = RecurringCommitment(
            user_id=user_id,
            kind=validated.kind,
            name=validated.name,
            provider=validated.provider,
            category=validated.category,
            amount=validated.amount,
            amount_kind=validated.amount_kind,
            currency_code=validated.currency_code,
            next_due_date=validated.next_due_date,
            frequency=validated.frequency,
            custom_interval_days=validated.custom_interval_days,
            recurrence_anchor_day=validated.next_due_date.day,
            auto_renews=validated.auto_renews,
            notes=validated.notes,
            created_via=validated.created_via,
            external_reference=validated.external_reference,
        )
        db.session.add(commitment)
        db.session.commit()
        return get_recurring_commitment_for_user(user_id, commitment.id) or commitment
    except IntegrityError as error:
        db.session.rollback()
        if validated.external_reference:
            existing = db.session.scalar(
                _commitment_select().where(
                    RecurringCommitment.user_id == user_id,
                    RecurringCommitment.created_via == validated.created_via,
                    RecurringCommitment.external_reference
                    == validated.external_reference,
                )
            )
            if existing is not None:
                return existing
        raise error
    except Exception:
        db.session.rollback()
        raise


def resolve_commitment_cycle_for_user(
    user_id: int,
    commitment_id: int,
    data: ResolveCommitmentCycleInput,
) -> RecurringCommitment | None:
    validated = _validate_resolution(data)

    try:
        commitment = get_recurring_commitment_for_user(
            user_id,
            commitment_id,
            for_update=True,
        )
        if commitment is None:
            db.session.rollback()
            return None
        if commitment.status != "active":
            raise RecurringCommitmentValidationError(
                "Reactivate this item before recording another cycle"
            )

        if validated.external_reference:
            existing_occurrence = db.session.scalar(
                select(CommitmentOccurrence).where(
                    CommitmentOccurrence.commitment_id == commitment_id,
                    CommitmentOccurrence.created_via == validated.created_via,
                    CommitmentOccurrence.external_reference
                    == validated.external_reference,
                )
            )
            if existing_occurrence is not None:
                db.session.rollback()
                return get_recurring_commitment_for_user(user_id, commitment_id)

        due_date = commitment.next_due_date
        commitment.occurrences.append(
            CommitmentOccurrence(
                resolution=validated.resolution,
                due_date=due_date,
                expected_amount=commitment.amount,
                actual_amount=validated.actual_amount,
                resolved_on=validated.resolved_on,
                notes=validated.notes,
                created_via=validated.created_via,
                external_reference=validated.external_reference,
            )
        )
        commitment.next_due_date = calculate_next_due_date(commitment)
        db.session.commit()
        return get_recurring_commitment_for_user(user_id, commitment_id)
    except IntegrityError as error:
        db.session.rollback()
        if validated.external_reference:
            existing_occurrence = db.session.scalar(
                select(CommitmentOccurrence).where(
                    CommitmentOccurrence.commitment_id == commitment_id,
                    CommitmentOccurrence.created_via == validated.created_via,
                    CommitmentOccurrence.external_reference
                    == validated.external_reference,
                )
            )
            if existing_occurrence is not None:
                return get_recurring_commitment_for_user(user_id, commitment_id)
        raise error
    except Exception:
        db.session.rollback()
        raise


def update_recurring_commitment_for_user(
    user_id: int,
    commitment_id: int,
    data: CreateRecurringCommitmentInput,
) -> RecurringCommitment | None:
    """Update future recurring-payment details without rewriting past cycles."""
    validated = _validate_create(data)

    try:
        commitment = get_recurring_commitment_for_user(
            user_id,
            commitment_id,
            for_update=True,
        )
        if commitment is None:
            db.session.rollback()
            return None

        commitment.kind = validated.kind
        commitment.name = validated.name
        commitment.provider = validated.provider
        commitment.category = validated.category
        commitment.amount = validated.amount
        commitment.amount_kind = validated.amount_kind
        commitment.currency_code = validated.currency_code
        commitment.next_due_date = validated.next_due_date
        commitment.frequency = validated.frequency
        commitment.custom_interval_days = validated.custom_interval_days
        commitment.recurrence_anchor_day = validated.next_due_date.day
        commitment.auto_renews = validated.auto_renews
        commitment.notes = validated.notes
        db.session.commit()
        return get_recurring_commitment_for_user(user_id, commitment_id)
    except Exception:
        db.session.rollback()
        raise


def update_commitment_occurrence_for_user(
    user_id: int,
    commitment_id: int,
    occurrence_id: int,
    data: ResolveCommitmentCycleInput,
) -> RecurringCommitment | None:
    """Correct a recorded paid/skipped cycle without advancing the schedule again."""
    validated = _validate_resolution(data)

    try:
        commitment = get_recurring_commitment_for_user(
            user_id,
            commitment_id,
            for_update=True,
        )
        if commitment is None:
            db.session.rollback()
            return None

        occurrence = next(
            (item for item in commitment.occurrences if item.id == occurrence_id),
            None,
        )
        if occurrence is None:
            db.session.rollback()
            return None

        occurrence.resolution = validated.resolution
        occurrence.actual_amount = validated.actual_amount
        occurrence.resolved_on = validated.resolved_on
        occurrence.notes = validated.notes
        db.session.commit()
        return get_recurring_commitment_for_user(user_id, commitment_id)
    except Exception:
        db.session.rollback()
        raise


def set_recurring_commitment_status_for_user(
    user_id: int,
    commitment_id: int,
    status: str,
) -> RecurringCommitment | None:
    normalized_status = str(status or "").strip().lower()
    if normalized_status not in {"active", "cancelled"}:
        raise RecurringCommitmentValidationError("Status must be active or cancelled")

    try:
        commitment = get_recurring_commitment_for_user(user_id, commitment_id)
        if commitment is None:
            return None
        commitment.status = normalized_status
        commitment.cancelled_at = (
            datetime.now(UTC) if normalized_status == "cancelled" else None
        )
        db.session.commit()
        return get_recurring_commitment_for_user(user_id, commitment_id)
    except Exception:
        db.session.rollback()
        raise


def archive_recurring_commitment_for_user(
    user_id: int,
    commitment_id: int,
) -> bool:
    try:
        commitment = get_recurring_commitment_for_user(user_id, commitment_id)
        if commitment is None:
            return False
        commitment.soft_delete()
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        raise

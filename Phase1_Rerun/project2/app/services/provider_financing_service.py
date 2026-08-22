from __future__ import annotations

import hashlib
import hmac
import re
from datetime import date

from flask import current_app
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.importers.contracts import ParsedFulizaNotice
from app.models.provider_financing_event import ProviderFinancingEvent


class DuplicateFinancingEventError(ValueError):
    def __init__(self, event_id: int):
        super().__init__("This financing notice has already been recorded.")
        self.event_id = event_id


def _fingerprint(message: str) -> str:
    secret = current_app.config["JWT_SECRET_KEY"].encode("utf-8")
    key = hmac.new(
        secret,
        b"moneytiq/provider-financing-fingerprint/v1",
        hashlib.sha256,
    ).digest()
    normalized = re.sub(r"\s+", " ", message.strip()).casefold().encode("utf-8")
    return hmac.new(key, normalized, hashlib.sha256).hexdigest()


def _find_existing(
    user_id: int,
    parsed: ParsedFulizaNotice,
    fingerprint: str,
) -> ProviderFinancingEvent | None:
    return db.session.scalar(
        select(ProviderFinancingEvent).where(
            ProviderFinancingEvent.user_id == user_id,
            or_(
                ProviderFinancingEvent.message_fingerprint == fingerprint,
                (
                    (ProviderFinancingEvent.provider == parsed.provider)
                    & (
                        ProviderFinancingEvent.external_reference
                        == parsed.external_reference
                    )
                    & (
                        ProviderFinancingEvent.event_type
                        == parsed.notice_type.value
                    )
                ),
            ),
        )
    )


def record_financing_notice_for_user(
    user_id: int,
    raw_message: str,
    parsed: ParsedFulizaNotice,
    *,
    recorded_on: date,
) -> ProviderFinancingEvent:
    fingerprint = _fingerprint(raw_message)
    existing = _find_existing(user_id, parsed, fingerprint)
    if existing is not None:
        raise DuplicateFinancingEventError(existing.id)

    event = ProviderFinancingEvent(
        user_id=user_id,
        provider=parsed.provider,
        external_reference=parsed.external_reference,
        message_fingerprint=fingerprint,
        event_type=parsed.notice_type.value,
        principal_amount=parsed.amount,
        currency_code=parsed.currency,
        financing_fee=parsed.financing_fee,
        daily_maintenance_fee=parsed.daily_maintenance_fee,
        outstanding_amount=parsed.outstanding_amount,
        due_date=parsed.due_date,
        occurred_at=None,
        recorded_on=recorded_on,
        settled_in_full=parsed.settled_in_full,
    )
    try:
        db.session.add(event)
        db.session.commit()
        return event
    except IntegrityError as error:
        db.session.rollback()
        existing = _find_existing(user_id, parsed, fingerprint)
        if existing is not None:
            raise DuplicateFinancingEventError(existing.id) from error
        raise
    except Exception:
        db.session.rollback()
        raise

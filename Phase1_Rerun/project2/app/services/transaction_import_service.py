import hashlib
import hmac
import re
from datetime import date

from flask import current_app
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.importers.contracts import ParsedTransactionMessage
from app.models.transaction_import import TransactionImport
from app.models.telegram_preferences import TelegramUserPreferences
from app.services.transaction_service import (
    build_transaction_for_user,
    rebuild_soft_deleted_transaction_for_user,
)


class TransactionMessageNotImportableError(ValueError):
    pass


class DuplicateTransactionImportError(ValueError):
    def __init__(self, transaction_id: int):
        super().__init__("This provider message has already been imported.")
        self.transaction_id = transaction_id


def payment_method_for_provider(provider: str) -> str:
    methods = {
        "mpesa": "m-pesa",
        "airtel_money": "airtel money",
    }
    try:
        return methods[provider]
    except KeyError as error:
        raise TransactionMessageNotImportableError(
            "This provider cannot create a transaction yet."
        ) from error


def _normalized_message(message: str) -> str:
    return re.sub(r"\s+", " ", message.strip()).casefold()


def message_fingerprint(provider: str, message: str) -> str:
    """Create a non-reversible duplicate key without storing the raw SMS.

    A purpose label separates this use of the application secret from JWT
    signing. The provider reference remains a second, stable duplicate guard.
    """

    secret = current_app.config["JWT_SECRET_KEY"].encode("utf-8")
    fingerprint_key = hmac.new(
        secret,
        b"moneytiq/transaction-import-fingerprint/v1",
        hashlib.sha256,
    ).digest()
    fingerprint_input = f"{provider}\0{_normalized_message(message)}".encode("utf-8")
    return hmac.new(fingerprint_key, fingerprint_input, hashlib.sha256).hexdigest()


def _find_existing_import(user_id: int, parsed: ParsedTransactionMessage, fingerprint: str) -> TransactionImport | None:
    return db.session.scalar(
        select(TransactionImport)
        .options(joinedload(TransactionImport.transaction))
        .where(
            TransactionImport.user_id == user_id,
            or_(
                (
                    (TransactionImport.provider == parsed.provider)
                    & (
                        TransactionImport.external_reference
                        == parsed.external_reference
                    )
                ),
                TransactionImport.message_fingerprint == fingerprint,
            ),
        )
    )


def _apply_import_provenance(
    import_record: TransactionImport,
    *,
    parsed: ParsedTransactionMessage,
    fingerprint: str,
) -> None:
    """Refresh non-sensitive provider facts from the newly parsed message."""
    import_record.provider = parsed.provider
    import_record.external_reference = parsed.external_reference
    import_record.message_fingerprint = fingerprint
    import_record.occurred_at = parsed.occurred_at
    import_record.provider_transaction_type = (
        parsed.provider_transaction_type or "unknown"
    )
    import_record.provider_flow = parsed.flow_direction.value
    import_record.currency_code = parsed.currency
    import_record.fee = parsed.fee
    import_record.fee_source = (
        "provider_reported" if parsed.fee is not None else "unknown"
    )
    import_record.original_estimated_fee = None
    import_record.fee_tariff_version = None


def _remember_category_alias(
    user_id: int,
    remember_alias: str | None,
    category_name: str,
) -> None:
    if not remember_alias:
        return
    preferences = db.session.get(TelegramUserPreferences, user_id)
    if preferences is None:
        preferences = TelegramUserPreferences(user_id=user_id)
        db.session.add(preferences)
    aliases = dict(preferences.category_aliases or {})
    aliases[remember_alias] = category_name
    preferences.category_aliases = aliases


def import_transaction_message_for_user(
    user_id: int,
    raw_message: str,
    parsed: ParsedTransactionMessage,
    transaction_date: date,
    description: str,
    category_name: str,
    transaction_type: str,
    remember_alias: str | None = None,
):
    """Parse and save the transaction plus provenance as one ACID operation."""

    fingerprint = message_fingerprint(parsed.provider, raw_message)
    existing = _find_existing_import(user_id, parsed, fingerprint)
    if existing is not None and existing.transaction.deleted_at is None:
        raise DuplicateTransactionImportError(existing.transaction_id)

    try:
        restored = existing is not None
        if existing is None:
            transaction = build_transaction_for_user(
                user_id=user_id,
                category_name=category_name,
                transaction_type=transaction_type,
                payment_method_name=payment_method_for_provider(parsed.provider),
                amount=parsed.amount,
                transaction_date=transaction_date,
                description=description,
                merchant_name=parsed.counterparty,
            )
            db.session.flush()
            import_record = TransactionImport(
                user_id=user_id,
                transaction_id=transaction.id,
            )
            db.session.add(import_record)
        else:
            import_record = existing
            transaction = rebuild_soft_deleted_transaction_for_user(
                existing.transaction,
                user_id=user_id,
                category_name=category_name,
                transaction_type=transaction_type,
                payment_method_name=payment_method_for_provider(parsed.provider),
                amount=parsed.amount,
                transaction_date=transaction_date,
                description=description,
                merchant_name=parsed.counterparty,
            )

        _apply_import_provenance(
            import_record,
            parsed=parsed,
            fingerprint=fingerprint,
        )
        _remember_category_alias(user_id, remember_alias, category_name)

        db.session.commit()
        return transaction, import_record, restored

    except IntegrityError as error:
        db.session.rollback()
        existing = _find_existing_import(user_id, parsed, fingerprint)
        if existing is not None:
            raise DuplicateTransactionImportError(
                existing.transaction_id
            ) from error
        raise
    except Exception:
        db.session.rollback()
        raise

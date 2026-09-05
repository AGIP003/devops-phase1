import hashlib
import hmac
import re
from datetime import date

from flask import current_app
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.importers.contracts import ParsedTransactionMessage
from app.models.transaction_import import TransactionImport
from app.models.telegram_preferences import TelegramUserPreferences
from app.services.transaction_service import build_transaction_for_user


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
        select(TransactionImport).where(
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
    if existing is not None:
        raise DuplicateTransactionImportError(existing.transaction_id)

    try:
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
            provider=parsed.provider,
            external_reference=parsed.external_reference,
            message_fingerprint=fingerprint,
            occurred_at=parsed.occurred_at,
            provider_transaction_type=parsed.provider_transaction_type or "unknown",
            provider_flow=parsed.flow_direction.value,
            currency_code=parsed.currency,
            fee=parsed.fee,
            fee_source=(
                "provider_reported"
                if parsed.fee is not None
                else "unknown"
            ),
        )
        db.session.add(import_record)

        if remember_alias:
            preferences = db.session.get(TelegramUserPreferences, user_id)
            if preferences is None:
                preferences = TelegramUserPreferences(user_id=user_id)
                db.session.add(preferences)
            aliases = dict(preferences.category_aliases or {})
            aliases[remember_alias] = category_name
            preferences.category_aliases = aliases

        db.session.commit()
        return transaction, import_record

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

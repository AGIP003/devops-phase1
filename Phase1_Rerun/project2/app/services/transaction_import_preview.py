from __future__ import annotations

import hashlib
import hmac

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import ValidationError

from app.importers.contracts import (
    ParsedTransactionMessage,
    TransactionClassification,
)
from app.schemas import ProviderImportSuggestion
from app.services.provider_import_ai import AIProviderImportResult
from app.services.transaction_import_service import message_fingerprint


PREVIEW_MAX_AGE_SECONDS = 10 * 60
PREVIEW_SALT = "moneytiq/provider-import-preview/v1"


class InvalidImportPreviewError(ValueError):
    pass


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        current_app.config["JWT_SECRET_KEY"],
        salt=PREVIEW_SALT,
        signer_kwargs={"digest_method": hashlib.sha256},
    )


def create_ai_import_preview_token(
    *,
    user_id: int,
    raw_message: str,
    result: AIProviderImportResult,
) -> str:
    if result.parsed is None or result.extraction.transaction is None:
        raise ValueError("A successful AI import result is required")

    parsed = result.parsed
    return _serializer().dumps({
        "version": 1,
        "userId": user_id,
        "messageFingerprint": message_fingerprint(
            parsed.provider,
            raw_message,
        ),
        "transaction": result.extraction.transaction.model_dump(mode="json"),
    })


def load_ai_import_preview_token(
    *,
    user_id: int,
    raw_message: str,
    token: str,
) -> ParsedTransactionMessage:
    if not isinstance(token, str) or not token.strip():
        raise InvalidImportPreviewError("AI import preview is missing")

    try:
        payload = _serializer().loads(
            token,
            max_age=PREVIEW_MAX_AGE_SECONDS,
        )
    except SignatureExpired as error:
        raise InvalidImportPreviewError(
            "AI import preview expired; preview the message again"
        ) from error
    except BadSignature as error:
        raise InvalidImportPreviewError("AI import preview is invalid") from error

    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise InvalidImportPreviewError("AI import preview is invalid")
    if payload.get("userId") != user_id:
        raise InvalidImportPreviewError(
            "AI import preview does not belong to this user"
        )

    try:
        suggestion = ProviderImportSuggestion.model_validate(
            payload.get("transaction")
        )
    except ValidationError as error:
        raise InvalidImportPreviewError(
            "AI import preview contains invalid transaction data"
        ) from error

    expected_fingerprint = message_fingerprint(
        suggestion.provider,
        raw_message,
    )
    supplied_fingerprint = str(payload.get("messageFingerprint") or "")
    if not hmac.compare_digest(expected_fingerprint, supplied_fingerprint):
        raise InvalidImportPreviewError(
            "AI import preview does not match this provider message"
        )

    return ParsedTransactionMessage(
        provider=suggestion.provider,
        external_reference=suggestion.external_reference,
        occurred_at=suggestion.occurred_at,
        amount=suggestion.amount,
        currency=suggestion.currency,
        flow_direction=suggestion.flow_direction,
        suggested_classification=(
            TransactionClassification.INCOME
            if suggestion.flow_direction.value == "money_in"
            else TransactionClassification.EXPENSE
        ),
        description=suggestion.description,
        counterparty=suggestion.counterparty,
        fee=suggestion.fee,
        resulting_balance=None,
        provider_transaction_type=suggestion.provider_transaction_type,
    )

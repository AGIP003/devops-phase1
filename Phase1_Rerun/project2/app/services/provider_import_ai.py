from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from time import perf_counter

from flask import current_app
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)
from pydantic import ValidationError

from app.importers.contracts import (
    ParsedTransactionMessage,
    ProviderFlowDirection,
    TransactionClassification,
)
from app.schemas import ProviderImportParseResult
from app.services.ai_support import (
    AIInvalidResponseError,
    AIServiceUnavailableError,
    AIUsageMetadata,
    build_usage_metadata,
    create_openai_client,
    get_ai_model,
    log_ai_invalid_response,
    log_ai_provider_failure,
)


logger = logging.getLogger(__name__)

MAX_PROVIDER_MESSAGE_CHARACTERS = 4000
PROVIDER_MESSAGE_PREFIX = re.compile(
    r"^\s*(?:TID:\s*)?[A-Z0-9]{10,11}"
    r"(?:\s+(?:confirmed|successful)\.|\.\s+)",
    re.IGNORECASE,
)

SYSTEM_PROMPT = """
Extract one completed M-Pesa or Airtel Money transaction from the supplied
provider message. The input has already had unnecessary sensitive fields
removed.

Rules:
- Never invent a reference, amount, provider, flow direction, date, fee, merchant,
  or transaction type.
- provider must be mpesa or airtel_money.
- currency must be KES.
- external_reference is the leading provider reference, not an account number.
- occurred_at must use ISO 8601 with Africa/Nairobi's +03:00 offset when the
  provider supplied a date and time; otherwise use null.
- fee is null when the provider did not state one.
- Do not include phone numbers, account numbers, wallet balances, links, or
  daily limits in description or counterparty.
- flow_direction must be money_in only for money received and money_out only
  for money paid, purchased, topped up, repaid, or sent.
- Reject failed, pending, reversed, ambiguous, withdrawal, transfer-between-
  account, financing, and loan-notice messages with can_parse=false.
- Use a short generic snake_case provider_transaction_type.
- Mark needs_review=true because this is a fallback after deterministic parsing
  failed.
- If any required financial fact is unclear, return can_parse=false with a
  short reason and transaction=null.
""".strip()


@dataclass(frozen=True, slots=True)
class AIProviderImportResult:
    extraction: ProviderImportParseResult
    parsed: ParsedTransactionMessage | None
    format_signature: str
    usage: AIUsageMetadata


def is_provider_message_candidate(message: str) -> bool:
    return bool(
        isinstance(message, str)
        and PROVIDER_MESSAGE_PREFIX.match(" ".join(message.strip().split()))
    )


def safe_format_signature(message: str) -> str:
    """Describe provider grammar without retaining personal message values."""

    clean = " ".join(message.casefold().split())
    prefix = re.match(r"^(?:tid:\s*)?([a-z0-9]{10,11})", clean)
    reference_length = len(prefix.group(1)) if prefix else 0
    provider_hint = "mpesa" if reference_length == 10 else "airtel"
    markers = [provider_hint]
    checks = (
        ("confirmed", r"\bconfirmed\b"),
        ("successful", r"\bsuccessful(?:ly)?\b"),
        ("sent_to", r"\bsent to\b"),
        ("paid_to", r"\bpaid to\b"),
        ("received_from", r"\breceived\b.+\bfrom\b"),
        ("for_account", r"\bfor account\b|\baccount\b"),
        ("transaction_cost", r"\btransaction cost\b"),
        ("fee", r"\bfee\b"),
        ("balance", r"\bbal(?:ance)?\b"),
    )
    markers.extend(label for label, pattern in checks if re.search(pattern, clean))
    return ":".join(markers)


def _provider_from_reference(reference: str) -> str:
    """Infer the SMS issuer from formats already enforced by our parsers."""

    if len(reference) == 10:
        return "mpesa"
    if len(reference) == 11:
        return "airtel_money"
    raise AIInvalidResponseError("Unsupported provider reference format")


def _explicit_flow_from_message(message: str) -> ProviderFlowDirection | None:
    """Read only explicit movement verbs; return None rather than guessing."""

    clean = " ".join(message.casefold().split())
    if re.search(r"\b(?:have\s+)?received\b.+\bfrom\b", clean):
        return ProviderFlowDirection.MONEY_IN
    if re.search(
        r"\b(?:sent\s+to|paid\s+to|successfully\s+paid\s+to|"
        r"purchase(?:d)?|top\s+up|loan\s+repayment)\b",
        clean,
    ):
        return ProviderFlowDirection.MONEY_OUT
    return None


def minimize_provider_message(message: str) -> str:
    """Remove fields the AI does not need while preserving transaction facts."""

    if not isinstance(message, str):
        raise ValueError("Provider message must be text")
    clean = " ".join(message.strip().split())
    if not clean:
        raise ValueError("Provider message cannot be empty")
    if len(clean) > MAX_PROVIDER_MESSAGE_CHARACTERS:
        raise ValueError(
            f"Provider message cannot exceed {MAX_PROVIDER_MESSAGE_CHARACTERS} characters"
        )
    if not is_provider_message_candidate(clean):
        raise ValueError("Text does not look like a completed provider message")

    clean = re.sub(r"https?://\S+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(
        r"\b(?:new\s+m-pesa\s+balance\s+is|your\s+m-pesa\s+balance\s+is|bal:)"
        r"\s*(?:ksh\s*)?\d[\d,]*(?:\.\d{1,2})?\.?",
        " [balance removed] ",
        clean,
        flags=re.IGNORECASE,
    )
    clean = re.sub(
        r"\bamount you can transact within the day is\s+"
        r"\d[\d,]*(?:\.\d{1,2})?\.?",
        " ",
        clean,
        flags=re.IGNORECASE,
    )
    clean = re.sub(
        r"\bMPESA ID:\s*[A-Z0-9]{10}\b",
        " ",
        clean,
        flags=re.IGNORECASE,
    )
    clean = re.sub(
        r"(?<!\d)(?:\+?254\d{9}|0[\d*]{9}|\d{9})(?!\d)",
        "[phone removed]",
        clean,
    )
    clean = re.sub(
        r"(\b(?:for\s+)?account\s+).+?(?=\s+on\s+\d{1,2}/)",
        r"\1[account removed]",
        clean,
        flags=re.IGNORECASE,
    )
    return " ".join(clean.split())


def parse_provider_message_with_ai(message: str) -> AIProviderImportResult:
    minimized = minimize_provider_message(message)
    signature = safe_format_signature(message)
    model = get_ai_model()
    client = create_openai_client()
    started_at = perf_counter()

    try:
        response = client.responses.parse(
            model=model,
            instructions=SYSTEM_PROMPT,
            input=minimized,
            text_format=ProviderImportParseResult,
            reasoning={"effort": current_app.config["AI_REASONING_EFFORT"]},
            max_output_tokens=current_app.config[
                "AI_TRANSACTION_MAX_OUTPUT_TOKENS"
            ],
            store=False,
        )
    except (
        APIConnectionError,
        APITimeoutError,
        RateLimitError,
        APIStatusError,
    ) as error:
        log_ai_provider_failure(
            logger,
            operation="provider_import_parse",
            error=error,
        )
        raise AIServiceUnavailableError(
            "AI provider-message parsing is temporarily unavailable"
        ) from error
    except (ValidationError, ValueError) as error:
        log_ai_invalid_response(
            logger,
            operation="provider_import_parse",
            reason=type(error).__name__,
        )
        raise AIInvalidResponseError(
            "AI returned an invalid provider-message response"
        ) from error

    if response.status != "completed" or response.output_parsed is None:
        reason = (
            f"status_{response.status}"
            if response.status != "completed"
            else "missing_parsed_output"
        )
        log_ai_invalid_response(
            logger,
            operation="provider_import_parse",
            reason=reason,
            provider_request_id=getattr(response, "_request_id", None),
        )
        raise AIInvalidResponseError(
            "AI provider-message response was incomplete"
        )

    extraction = response.output_parsed
    suggestion = extraction.transaction
    parsed = None
    if extraction.can_parse and suggestion is not None:
        reference_match = re.match(
            r"^\s*(?:TID:\s*)?(?P<reference>[A-Z0-9]{10,11})",
            message,
            re.IGNORECASE,
        )
        source_reference = (
            reference_match["reference"].upper()
            if reference_match is not None
            else None
        )
        if suggestion.external_reference != source_reference:
            log_ai_invalid_response(
                logger,
                operation="provider_import_parse",
                reason="reference_mismatch",
                provider_request_id=getattr(response, "_request_id", None),
            )
            raise AIInvalidResponseError(
                "AI returned a mismatched provider reference"
            )
        expected_provider = _provider_from_reference(source_reference)
        if suggestion.provider != expected_provider:
            log_ai_invalid_response(
                logger,
                operation="provider_import_parse",
                reason="provider_mismatch",
                provider_request_id=getattr(response, "_request_id", None),
            )
            raise AIInvalidResponseError(
                "AI returned a provider that conflicts with the message format"
            )
        explicit_flow = _explicit_flow_from_message(message)
        if (
            explicit_flow is not None
            and suggestion.flow_direction is not explicit_flow
        ):
            log_ai_invalid_response(
                logger,
                operation="provider_import_parse",
                reason="flow_mismatch",
                provider_request_id=getattr(response, "_request_id", None),
            )
            raise AIInvalidResponseError(
                "AI returned a direction that conflicts with the provider wording"
            )
        suggested_classification = (
            TransactionClassification.INCOME
            if suggestion.flow_direction is ProviderFlowDirection.MONEY_IN
            else TransactionClassification.EXPENSE
        )
        parsed = ParsedTransactionMessage(
            provider=suggestion.provider,
            external_reference=suggestion.external_reference,
            occurred_at=suggestion.occurred_at,
            amount=suggestion.amount,
            currency=suggestion.currency,
            flow_direction=suggestion.flow_direction,
            suggested_classification=suggested_classification,
            description=suggestion.description,
            counterparty=suggestion.counterparty,
            fee=suggestion.fee,
            resulting_balance=None,
            provider_transaction_type=suggestion.provider_transaction_type,
        )

    return AIProviderImportResult(
        extraction=extraction,
        parsed=parsed,
        format_signature=signature,
        usage=build_usage_metadata(
            response,
            model=model,
            started_at=started_at,
        ),
    )

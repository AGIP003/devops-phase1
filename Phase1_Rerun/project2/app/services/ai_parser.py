from __future__ import annotations

import logging
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

from app.schemas import TransactionParseResult
from app.services.ai_support import (
    AIInvalidResponseError,
    AIServiceUnavailableError,
    AIUsageMetadata,
    build_usage_metadata,
    create_openai_client,
    get_ai_model,
)
from finance_tracker.utils.validations import (
    ALLOWED_TRANSACTION_CATEGORIES,
)


logger = logging.getLogger(__name__)

MAX_TRANSACTION_TEXT_CHARACTERS = 500

INCOME_CATEGORIES = ", ".join(
    ALLOWED_TRANSACTION_CATEGORIES["income"]
)
EXPENSE_CATEGORIES = ", ".join(
    ALLOWED_TRANSACTION_CATEGORIES["expense"]
)

SYSTEM_PROMPT = f"""
Extract one personal-finance transaction from the user's message.

The message may contain English, Swahili, Sheng, or a noisy voice
transcript.

Income categories:
{INCOME_CATEGORIES}

Expense categories:
{EXPENSE_CATEGORIES}

Rules:
- Preserve the explicitly stated three-letter currency code.
- Use KES only when the message gives no other currency.
- Never convert currencies.
- Never invent an amount, transaction kind, description, or category.
- The category must belong to the selected transaction kind.
- If required information is missing or ambiguous, return can_parse=false,
  transaction=null, and a short reason.
- If parsing succeeds, return can_parse=true, reason=null, and the transaction.
- Set needs_review=true whenever wording, currency, category, or intent is
  ambiguous.
- Confidence describes uncertainty but never authorizes saving.
""".strip()


@dataclass(frozen=True, slots=True)
class AITransactionParseResult:
    extraction: TransactionParseResult
    usage: AIUsageMetadata


def normalize_transaction_input(text: str) -> str:
    if not isinstance(text, str):
        raise ValueError("Transaction text must be a string")

    clean_text = " ".join(text.strip().split())

    if not clean_text:
        raise ValueError("Transaction text cannot be empty")

    if len(clean_text) > MAX_TRANSACTION_TEXT_CHARACTERS:
        raise ValueError(
            "Transaction text cannot exceed "
            f"{MAX_TRANSACTION_TEXT_CHARACTERS} characters"
        )

    return clean_text


def parse_with_ai(text: str) -> AITransactionParseResult:
    clean_text = normalize_transaction_input(text)
    model = get_ai_model()
    client = create_openai_client()
    started_at = perf_counter()

    try:
        response = client.responses.parse(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": clean_text,
                },
            ],
            text_format=TransactionParseResult,
            reasoning={
                "effort": current_app.config[
                    "AI_REASONING_EFFORT"
                ],
            },
            max_output_tokens=current_app.config[
                "AI_TRANSACTION_MAX_OUTPUT_TOKENS"
            ],
            store=False,
        )
    except (
        APIConnectionError,
        APITimeoutError,
        RateLimitError,
    ) as error:
        logger.warning(
            "AI transaction service unavailable",
            extra={"error_type": type(error).__name__},
        )
        raise AIServiceUnavailableError(
            "AI transaction parsing is temporarily unavailable"
        ) from error
    except APIStatusError as error:
        logger.warning(
            "AI transaction provider returned an error",
            extra={
                "status_code": error.status_code,
                "error_type": type(error).__name__,
            },
        )
        raise AIServiceUnavailableError(
            "AI transaction parsing is temporarily unavailable"
        ) from error
    except (ValidationError, ValueError) as error:
        logger.warning(
            "AI transaction response failed validation",
            extra={"error_type": type(error).__name__},
        )
        raise AIInvalidResponseError(
            "AI returned an invalid transaction response"
        ) from error

    if response.status != "completed":
        raise AIInvalidResponseError(
            f"AI transaction response ended with status {response.status!r}"
        )

    extraction = response.output_parsed
    if extraction is None:
        raise AIInvalidResponseError(
            "AI transaction response contained no parsed output"
        )

    if extraction.can_parse and extraction.transaction is not None:
        transaction = extraction.transaction
        allowed_categories = ALLOWED_TRANSACTION_CATEGORIES[
            transaction.kind.value
        ]
        if transaction.category not in allowed_categories:
            raise AIInvalidResponseError(
                "AI returned an unsupported transaction category"
            )

    return AITransactionParseResult(
        extraction=extraction,
        usage=build_usage_metadata(
            response,
            model=model,
            started_at=started_at,
        ),
    )

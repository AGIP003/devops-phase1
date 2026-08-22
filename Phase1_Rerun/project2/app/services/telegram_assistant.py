from __future__ import annotations

import hmac
import logging
from dataclasses import dataclass
from hashlib import sha256
from time import perf_counter

from flask import current_app
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)
from pydantic import ValidationError

from app.schemas import TelegramAssistantResponse
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

MAX_ASSISTANT_TEXT_CHARACTERS = 500

INCOME_CATEGORIES = ", ".join(
    ALLOWED_TRANSACTION_CATEGORIES["income"]
)
EXPENSE_CATEGORIES = ", ".join(
    ALLOWED_TRANSACTION_CATEGORIES["expense"]
)

ASSISTANT_PROMPT = f"""
Route and answer one message sent to the Moneytiqx personal-finance Telegram
bot.

Available bot functions:
- /add AMOUNT DESCRIPTION prepares a manually entered transaction.
- A pasted M-Pesa or Airtel Money SMS is handled separately by a strict parser.
- A receipt photo can be read and reviewed before saving.
- /balance shows recorded income, expenses and balance.
- /default PAYMENT changes the default payment method.
- /alias WORD=CATEGORY saves a personal category alias.
- /help lists commands.

Income categories:
{INCOME_CATEGORIES}

Expense categories:
{EXPENSE_CATEGORIES}

Routing rules:
- Use transaction only when the user clearly describes one transaction and
  supplies a positive amount and meaningful description.
- Use balance when the user asks for their balance, income, expenses or current
  financial summary. Do not invent those values; the application will load
  them from its database.
- Use analytics when the user asks about recorded spending searches, merchants,
  fees, changes between periods, commitments, goals, debts or what-if scenarios.
  A separate ownership-filtered analytics service will obtain the facts.
- Use help for greetings and questions about using the bot.
- Use finance_education for short general personal-finance explanations.
- Use unsupported for unrelated requests, requests for current market facts,
  or requests requiring data the bot does not have.

Safety and response rules:
- Never claim that anything was saved, changed or deleted.
- Never invent the user's balances, transactions, goals or other private data.
- Do not provide personalized investment, legal or tax instructions.
- Present choices and trade-offs; the user makes financial decisions.
- Never request a password, token, PIN, card number or full account number.
- Preserve an explicitly stated three-letter currency code. Use KES only when
  no currency is stated. Never convert currencies.
- A transaction category must belong to its transaction kind.
- Set needs_review=true when transaction wording, category, currency or intent
  is uncertain.
- Keep reply concise, plain text and useful in Telegram.
""".strip()


@dataclass(frozen=True, slots=True)
class AITelegramAssistantResult:
    response: TelegramAssistantResponse
    usage: AIUsageMetadata


def normalize_assistant_input(text: str) -> str:
    if not isinstance(text, str):
        raise ValueError("Assistant text must be a string")

    clean_text = " ".join(text.strip().split())
    if not clean_text:
        raise ValueError("Assistant text cannot be empty")
    if len(clean_text) > MAX_ASSISTANT_TEXT_CHARACTERS:
        raise ValueError(
            "Assistant text cannot exceed "
            f"{MAX_ASSISTANT_TEXT_CHARACTERS} characters"
        )
    return clean_text


def _safety_identifier(user_id: int) -> str:
    """Create a stable provider identifier without exposing our user ID."""

    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(
        secret,
        f"telegram-assistant:{user_id}".encode("utf-8"),
        sha256,
    ).hexdigest()


def respond_to_telegram_message(
    text: str,
    *,
    user_id: int,
) -> AITelegramAssistantResult:
    clean_text = normalize_assistant_input(text)
    model = get_ai_model()
    client = create_openai_client()
    started_at = perf_counter()

    try:
        provider_response = client.responses.parse(
            model=model,
            instructions=ASSISTANT_PROMPT,
            input=clean_text,
            text_format=TelegramAssistantResponse,
            reasoning={
                "effort": current_app.config["AI_REASONING_EFFORT"],
            },
            max_output_tokens=current_app.config[
                "AI_ASSISTANT_MAX_OUTPUT_TOKENS"
            ],
            safety_identifier=_safety_identifier(user_id),
            store=False,
        )
    except (
        APIConnectionError,
        APITimeoutError,
        RateLimitError,
    ) as error:
        logger.warning(
            "AI Telegram assistant unavailable",
            extra={"error_type": type(error).__name__},
        )
        raise AIServiceUnavailableError(
            "AI assistance is temporarily unavailable"
        ) from error
    except APIStatusError as error:
        logger.warning(
            "AI Telegram assistant provider returned an error",
            extra={
                "status_code": error.status_code,
                "error_type": type(error).__name__,
            },
        )
        raise AIServiceUnavailableError(
            "AI assistance is temporarily unavailable"
        ) from error
    except (ValidationError, ValueError) as error:
        logger.warning(
            "AI Telegram assistant response failed validation",
            extra={"error_type": type(error).__name__},
        )
        raise AIInvalidResponseError(
            "AI returned an invalid Telegram response"
        ) from error

    if provider_response.status != "completed":
        raise AIInvalidResponseError(
            "AI Telegram response ended with status "
            f"{provider_response.status!r}"
        )

    parsed = provider_response.output_parsed
    if parsed is None:
        raise AIInvalidResponseError(
            "AI Telegram response contained no parsed output"
        )

    if parsed.transaction is not None:
        allowed_categories = ALLOWED_TRANSACTION_CATEGORIES[
            parsed.transaction.kind.value
        ]
        if parsed.transaction.category not in allowed_categories:
            raise AIInvalidResponseError(
                "AI returned an unsupported transaction category"
            )

    return AITelegramAssistantResult(
        response=parsed,
        usage=build_usage_metadata(
            provider_response,
            model=model,
            started_at=started_at,
        ),
    )

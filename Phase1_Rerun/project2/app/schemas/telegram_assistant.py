from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.schemas.parsed_transaction import TransactionSuggestion


class TelegramAssistantIntent(StrEnum):
    """Actions the Telegram bot is allowed to take after AI routing."""

    TRANSACTION = "transaction"
    BALANCE = "balance"
    ANALYTICS = "analytics"
    HELP = "help"
    FINANCE_EDUCATION = "finance_education"
    UNSUPPORTED = "unsupported"


class TelegramAssistantResponse(BaseModel):
    """Validated boundary between model output and Telegram behavior."""

    intent: TelegramAssistantIntent
    reply: str = Field(min_length=1, max_length=700)
    transaction: TransactionSuggestion | None = None

    @model_validator(mode="after")
    def validate_intent_payload(self):
        if self.intent == TelegramAssistantIntent.TRANSACTION:
            if self.transaction is None:
                raise ValueError(
                    "A transaction intent must contain a transaction"
                )
        elif self.transaction is not None:
            raise ValueError(
                "Only a transaction intent may contain a transaction"
            )

        return self

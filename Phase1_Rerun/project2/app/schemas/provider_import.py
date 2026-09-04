from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.money import AIMoney
from app.schemas.parsed_transaction import TransactionKind


class ProviderImportSuggestion(BaseModel):
    """Import evidence extracted from one mobile-money provider message."""

    provider: Literal["mpesa", "airtel_money"]
    external_reference: str = Field(pattern=r"^[A-Z0-9]{10,11}$")
    occurred_at: datetime | None
    amount: AIMoney = Field(gt=0, max_digits=12, decimal_places=2)
    currency: Literal["KES"]
    direction: TransactionKind
    description: str = Field(min_length=1, max_length=200)
    counterparty: str | None = Field(default=None, max_length=100)
    fee: AIMoney | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    provider_transaction_type: str = Field(
        min_length=2,
        max_length=40,
        pattern=r"^[a-z0-9_]+$",
    )
    confidence: float = Field(ge=0, le=1)
    needs_review: Literal[True]

    @field_validator("external_reference", mode="before")
    @classmethod
    def normalize_reference(cls, value: object) -> str:
        return str(value).strip().upper()

    @field_validator("description", "counterparty", mode="before")
    @classmethod
    def normalize_text(cls, value: object):
        if value is None:
            return None
        return " ".join(str(value).strip().split())

    @field_validator("provider_transaction_type", mode="before")
    @classmethod
    def normalize_transaction_type(cls, value: object) -> str:
        return "_".join(str(value).strip().lower().split())

    @field_validator("occurred_at")
    @classmethod
    def require_explicit_timezone(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("Provider transaction time must include a timezone")
        return value


class ProviderImportParseResult(BaseModel):
    can_parse: bool
    reason: str | None
    transaction: ProviderImportSuggestion | None

    @model_validator(mode="after")
    def validate_result_state(self):
        if self.can_parse:
            if self.transaction is None:
                raise ValueError(
                    "A parseable provider message must contain a transaction"
                )
            if self.reason is not None:
                raise ValueError(
                    "A successful provider parse must not contain a failure reason"
                )
        else:
            if self.transaction is not None:
                raise ValueError(
                    "An unsuccessful provider parse must not contain a transaction"
                )
            if not self.reason or not self.reason.strip():
                raise ValueError(
                    "An unsuccessful provider parse must explain why"
                )
        return self

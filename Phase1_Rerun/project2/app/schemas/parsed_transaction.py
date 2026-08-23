from __future__ import annotations

from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.money import AIMoney


class TransactionKind(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"


class TransactionSuggestion(BaseModel):
    kind: TransactionKind
    amount: AIMoney = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(min_length=2, max_length=40)
    description: str = Field(min_length=1, max_length=200)
    currency: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    ) 
    confidence: float = Field(ge=0, le=1)
    needs_review: bool 
     
    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: object) -> str:
        return " ".join(str(value).strip().split())

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> str:
        return str(value).strip().upper()

class TransactionParseResult(BaseModel):
    can_parse: bool
    reason: str | None
    transaction: TransactionSuggestion | None

    @model_validator(mode="after")
    def validate_result_state(self):
        if self.can_parse:
            if self.transaction is None:
                raise ValueError(
                    "A parseable result must contain a transaction"
                )
            if self.reason is not None:
                raise ValueError(
                    "A successful result must not contain a failure reason"
                )
        else:
            if self.transaction is not None:
                raise ValueError(
                    "An unsuccessful result must not contain a transaction"
                )
            if not self.reason or not self.reason.strip():
                raise ValueError(
                    "An unsuccessful result must explain why"
                )

        return self

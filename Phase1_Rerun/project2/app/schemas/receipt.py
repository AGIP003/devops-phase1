from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.money import AIMoney


class ReceiptLineItem(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    quantity: AIMoney | None
    total: AIMoney | None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> str:
        return " ".join(str(value).strip().split())

class ReceiptSuggestion(BaseModel):
    merchant: str = Field(min_length=1, max_length=120)
    total: AIMoney = Field(gt=0, max_digits=12, decimal_places=2)
    transaction_date: date | None
    currency: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )
    suggested_category: str = Field(min_length=2, max_length=40)
    items: list[ReceiptLineItem] = Field(max_length=40)
    confidence: float = Field(ge=0, le=1)
    needs_review: bool

    @field_validator("merchant", mode="before")
    @classmethod
    def normalize_merchant(cls, value:object) -> str:
        return " ".join(str(value).strip().split())

    @field_validator("suggested_category", mode="before")
    @classmethod
    def normalize_category(cls, value: object) -> str:
        return str(value).strip().lower()
    
    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> str:
        return str(value).strip().upper()

class ReceiptParseResult(BaseModel):
    can_parse: bool
    reason: str | None
    receipt: ReceiptSuggestion | None

    @model_validator(mode="after")
    def validate_result_state(self):
        if self.can_parse:
            if self.receipt is None:
                raise ValueError(
                    "A parseable result must contain a receipt"
                )
            if self.reason is not None:
                raise ValueError(
                    "A successful result must not contain a failure reason"
                )
        else:
            if self.receipt is not None:
                raise ValueError(
                    "An unsuccessful result must not contain a receipt"
                )
            if not self.reason or not self.reason.strip():
                raise ValueError(
                    "An unsuccessful result must contain a failure reason"
                )
        
        return self

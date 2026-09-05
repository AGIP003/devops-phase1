from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum


class TransactionClassification(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class ProviderFlowDirection(StrEnum):
    """The movement explicitly reported by the provider message."""

    MONEY_IN = "money_in"
    MONEY_OUT = "money_out"


class FulizaNoticeType(StrEnum):
    DRAW = "draw"
    REPAYMENT = "repayment"


@dataclass(frozen=True, slots=True)
class ParsedTransactionMessage:
    provider: str
    external_reference: str
    occurred_at: datetime | None
    amount: Decimal
    currency: str
    flow_direction: ProviderFlowDirection
    suggested_classification: TransactionClassification
    description: str
    counterparty: str | None = None
    fee: Decimal | None = None
    resulting_balance: Decimal | None = None
    provider_transaction_type: str | None = None
    network_reference: str | None = None


@dataclass(frozen=True, slots=True)
class ParsedFulizaNotice:
    provider: str
    external_reference: str
    notice_type: FulizaNoticeType
    amount: Decimal
    currency: str
    financing_fee: Decimal | None = None
    daily_maintenance_fee: Decimal | None = None
    outstanding_amount: Decimal | None = None
    due_date: date | None = None
    settled_in_full: bool | None = None

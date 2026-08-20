import re
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.importers.contracts import (
    ParsedTransactionMessage,
    TransactionDirection,
)


NAIROBI_TIMEZONE = ZoneInfo("Africa/Nairobi")


SENT_MONEY_PATTERN = re.compile(
    r"^(?P<reference>[A-Z0-9]{10})\s+Confirmed\.\s+"
    r"Ksh(?P<amount>[\d,]+\.\d{2})\s+sent to\s+"
    r"(?P<counterparty>.+?)\s+(?:254|0)\d{9}\s+on\s+"
    r"(?P<date>\d{1,2}/\d{1,2}/\d{2})\s+at\s+"
    r"(?P<time>\d{1,2}:\d{2}\s+[AP]M)\.\s+"
    r"New M-PESA balance is Ksh(?P<balance>[\d,]+\.\d{2})\.\s+"
    r"Transaction cost,\s*Ksh(?P<fee>[\d,]+\.\d{2})\.$",
    re.IGNORECASE,
)

RECEIVED_MONEY_PATTERN = re.compile(
    r"^(?P<reference>[A-Z0-9]{10})\s+Confirmed\.\s*"
    r"You have received Ksh(?P<amount>[\d,]+\.\d{2})\s+from\s+"
    r"(?P<counterparty>.+?)\s+(?:254|0)\d{9}\s+on\s+"
    r"(?P<date>\d{1,2}/\d{1,2}/\d{2})\s+at\s+"
    r"(?P<time>\d{1,2}:\d{2}\s+[AP]M)\.\s+"
    r"New M-PESA balance is Ksh(?P<balance>[\d,]+\.\d{2})\.$",
    re.IGNORECASE,
)

PAYBILL_PATTERN = re.compile(
    r"^(?P<reference>[A-Z0-9]{10})\s+Confirmed\.\s*"
    r"Ksh\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?)\s+sent to\s+"
    r"(?P<counterparty>.+?)(?:\.\s+|\s+)for account\s+"
    r"(?P<account_reference>.+?)\s+on\s+"
    r"(?P<date>\d{1,2}/\d{1,2}/\d{2})\s+at\s+"
    r"(?P<time>\d{1,2}:\d{2}\s*[AP]M)\.?\s*"
    r"New M-PESA balance is Ksh\s*(?P<balance>\d[\d,]*(?:\.\d{1,2})?)\.\s*"
    r"Transaction cost,\s*Ksh\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\."
    r"(?:\s*Amount you can transact within the day is\s+"
    r"\d[\d,]*(?:\.\d{1,2})?\.)?"
    r"(?:\s*Download My OneApp on https?://\S+)?$",
    re.IGNORECASE,
)

AIRTIME_PATTERN = re.compile(
    r"^(?P<reference>[A-Z0-9]{10})\s+Confirmed\.\s*"
    r"You bought Ksh\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?)\s+"
    r"of airtime\s+on\s+"
    r"(?P<date>\d{1,2}/\d{1,2}/\d{2})\s+at\s+"
    r"(?P<time>\d{1,2}:\d{2}\s*[AP]M)\.?\s*"
    r"New M-PESA balance is Ksh\s*(?P<balance>\d[\d,]*(?:\.\d{1,2})?)\.\s*"
    r"Transaction cost,\s*Ksh\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\."
    r"(?:\s*Amount you can transact within the day is\s+"
    r"\d[\d,]*(?:\.\d{1,2})?\.)?"
    r"(?:\s*Download My OneApp on https?://\S+)?$",
    re.IGNORECASE,
)

WITHDRAWAL_PATTERN = re.compile(
    r"^(?P<reference>[A-Z0-9]{10})\s+Confirmed\.\s*on\s+"
    r"(?P<date>\d{1,2}/\d{1,2}/\d{2})\s+at\s+"
    r"(?P<time>\d{1,2}:\d{2}\s*[AP]M)\s*"
    r"Withdraw Ksh\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?)\s+from\s+"
    r"\d+\s+-\s+(?P<counterparty>.+?)\s+"
    r"New M-PESA balance is Ksh\s*(?P<balance>\d[\d,]*(?:\.\d{1,2})?)\.\s*"
    r"Transaction cost,\s*Ksh\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\."
    r"(?:\s*Amount you can transact within the day is\s+"
    r"\d[\d,]*(?:\.\d{1,2})?\.)?"
    r"(?:\s*Get a Lipa Na M-PESA Till online:\s*https?://\S+)?$",
    re.IGNORECASE,
)

class MpesaMessageParseError(ValueError):
    pass

def _parse_occurred_at(match: re.Match) -> datetime:
    return datetime.strptime(
        f"{match['date']} {match['time']}",
        "%d/%m/%y %I:%M %p",
    ).replace(tzinfo=NAIROBI_TIMEZONE)

def _parse_money(value: str) -> Decimal:
    return Decimal(value.replace(",", ""))


def parse_mpesa_message(message: str) -> ParsedTransactionMessage:
    clean_message = message.strip()

    sent_match = SENT_MONEY_PATTERN.fullmatch(clean_message)

    if sent_match is not None:
        counterparty = sent_match["counterparty"].strip()

        return ParsedTransactionMessage(
            provider="mpesa",
            external_reference=sent_match["reference"].upper(),
            occurred_at=_parse_occurred_at(sent_match),
            amount=_parse_money(sent_match["amount"]),
            currency="KES",
            direction=TransactionDirection.EXPENSE,
            description=f"Sent to {counterparty}",
            counterparty=counterparty,
            fee=_parse_money(sent_match["fee"]),
            resulting_balance=_parse_money(sent_match["balance"]),
            provider_transaction_type="send_money",
        )

    received_match = RECEIVED_MONEY_PATTERN.fullmatch(clean_message)

    if received_match is not None:
        counterparty = received_match["counterparty"].strip()
        return ParsedTransactionMessage(
            provider="mpesa",
            external_reference=received_match["reference"].upper(),
            occurred_at=_parse_occurred_at(received_match),
            amount=_parse_money(received_match["amount"]),
            currency="KES",
            direction=TransactionDirection.INCOME,
            description=f"Received from {counterparty}",
            counterparty=counterparty,
            fee=None,
            resulting_balance=_parse_money(received_match["balance"]),
            provider_transaction_type="received_money",
        )

    paybill_match = PAYBILL_PATTERN.fullmatch(clean_message)

    if paybill_match is not None:
        counterparty = paybill_match["counterparty"].strip()
        provider_transaction_type = (
            "data_bundle"
            if re.search(r"\bdata\s+bundles?\b", counterparty, re.IGNORECASE)
            else "paybill"
        )

        return ParsedTransactionMessage(
            provider="mpesa",
            external_reference=paybill_match["reference"].upper(),
            occurred_at=_parse_occurred_at(paybill_match),
            amount=_parse_money(paybill_match["amount"]),
            currency="KES",
            direction=TransactionDirection.EXPENSE,
            description=f"Paid {counterparty}",
            counterparty=counterparty,
            fee=_parse_money(paybill_match["fee"]),
            resulting_balance=_parse_money(paybill_match["balance"]),
            provider_transaction_type=provider_transaction_type,
        )

    airtime_match = AIRTIME_PATTERN.fullmatch(clean_message)

    if airtime_match is not None:
        return ParsedTransactionMessage(
            provider="mpesa",
            external_reference=airtime_match["reference"].upper(),
            occurred_at=_parse_occurred_at(airtime_match),
            amount=_parse_money(airtime_match["amount"]),
            currency="KES",
            direction=TransactionDirection.EXPENSE,
            description="Safaricom airtime",
            counterparty="Safaricom",
            fee=_parse_money(airtime_match["fee"]),
            resulting_balance=_parse_money(airtime_match["balance"]),
            provider_transaction_type="airtime",
        )

    withdrawal_match = WITHDRAWAL_PATTERN.fullmatch(clean_message)

    if withdrawal_match is not None:
        counterparty = withdrawal_match["counterparty"].strip()

        return ParsedTransactionMessage(
            provider="mpesa",
            external_reference=withdrawal_match["reference"].upper(),
            occurred_at=_parse_occurred_at(withdrawal_match),
            amount=_parse_money(withdrawal_match["amount"]),
            currency="KES",
            direction=TransactionDirection.TRANSFER,
            description=f"Cash withdrawal at {counterparty}",
            counterparty=counterparty,
            fee=_parse_money(withdrawal_match["fee"]),
            resulting_balance=_parse_money(withdrawal_match["balance"]),
            provider_transaction_type="withdrawal",
        )

    raise MpesaMessageParseError("Unsupported M-Pesa message format.")

import re
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.importers.contracts import (
    ParsedTransactionMessage,
    TransactionDirection,
)


NAIROBI_TIMEZONE = ZoneInfo("Africa/Nairobi")
MONEY_PATTERN = r"\d[\d,]*(?:\.\d{1,2})?"
PHONE_PATTERN = r"(?:254\d{9}|0?\d{9})"


SENT_MONEY_PATTERN = re.compile(
    rf"^(?P<reference>[A-Z0-9]{{11}})\.\s*"
    rf"Ksh\s*(?P<amount>{MONEY_PATTERN})\s+sent to\s+"
    rf"(?P<counterparty>.+?)\s+{PHONE_PATTERN}\s+on\s+"
    rf"(?P<date>\d{{1,2}}/\d{{1,2}}/\d{{2,4}})\s+at\s+"
    rf"(?P<time>\d{{1,2}}:\d{{2}}\s*[AP]M)\.\s*"
    rf"Fee:\s*Ksh\s*(?P<fee>{MONEY_PATTERN})\.\s*"
    rf"Bal:\s*Ksh\s*(?P<balance>{MONEY_PATTERN})\.\s*"
    r"MPESA ID:\s*(?P<network_reference>[A-Z0-9]{10})$",
    re.IGNORECASE,
)

RECEIVED_MONEY_PATTERN = re.compile(
    rf"^TID:\s*(?P<reference>[A-Z0-9]{{11}})\.\s*"
    rf"Received Ksh\s*(?P<amount>{MONEY_PATTERN})\s+from\s+"
    rf"(?P<counterparty>.+?)\s+{PHONE_PATTERN}\s+on\s+"
    rf"(?P<date>\d{{1,2}}/\d{{1,2}}/\d{{2,4}})\s+"
    rf"(?P<time>\d{{1,2}}:\d{{2}}\s*[AP]M)\.\s*"
    rf"Bal:\s*Ksh\s*(?P<balance>{MONEY_PATTERN})\s+"
    r"Sender TID:\s*(?P<network_reference>[A-Z0-9]{10})\.$",
    re.IGNORECASE,
)

BUNDLE_PATTERN = re.compile(
    rf"^(?P<reference>[A-Z0-9]{{11}})\s+Confirmed\.\s*"
    rf"Bundle purchase successful of Ksh\s*(?P<amount>{MONEY_PATTERN})\s+via\s+"
    r"(?P<counterparty>.+?)\s+on\s+"
    rf"(?P<date>\d{{1,2}}/\d{{1,2}}/\d{{2,4}})\s+at\s+"
    rf"(?P<time>\d{{1,2}}:\d{{2}}\s*[AP]M)\.\s*"
    rf"Bal:\s*Ksh\s*(?P<balance>{MONEY_PATTERN})\.$",
    re.IGNORECASE,
)

AIRTIME_TOPUP_PATTERN = re.compile(
    rf"^(?P<reference>[A-Z0-9]{{11}})\s+Successful\.\s*"
    rf"Airtime top up of Ksh\s*(?P<amount>{MONEY_PATTERN})\s+to\s+"
    rf"{PHONE_PATTERN}\.\s*"
    rf"Bal:\s*Ksh\s*(?P<balance>{MONEY_PATTERN})\.$",
    re.IGNORECASE,
)

AIRTIME_TOPUP_FOR_LINE_PATTERN = re.compile(
    rf"^(?P<reference>[A-Z0-9]{{11}})\s+Successful\.\s*"
    rf"Airtime top up for line\s+{PHONE_PATTERN}\s+of\s+"
    rf"Ksh\s*(?P<amount>{MONEY_PATTERN})\s+is successful\.\s*"
    rf"Bal:\s*Ksh\s*(?P<balance>{MONEY_PATTERN})\."
    r"(?:\s*To check your airtime balance,\s*dial\s+\*131#)?$",
    re.IGNORECASE,
)

PAYBILL_PATTERN = re.compile(
    rf"^(?P<reference>[A-Z0-9]{{11}})\.\s*"
    rf"Ksh\s*(?P<amount>{MONEY_PATTERN})\s+paid to\s+"
    r"(?P<counterparty>.+?)\s+account\s+"
    rf"(?P<account_reference>\S+)\s+on\s+"
    rf"(?P<date>\d{{1,2}}/\d{{1,2}}/\d{{2,4}})\s+"
    rf"(?P<time>\d{{1,2}}:\d{{2}})\.\s*"
    rf"Fee:?\s*Ksh\s*(?P<fee>{MONEY_PATTERN})\.\s*"
    rf"Bal:\s*Ksh\s*(?P<balance>{MONEY_PATTERN})\.\s*"
    r"MPESA ID:\s*(?P<network_reference>[A-Z0-9]{10})$",
    re.IGNORECASE,
)


class AirtelMoneyMessageParseError(ValueError):
    pass


def _parse_money(value: str) -> Decimal:
    return Decimal(value.replace(",", ""))


def _normalize_counterparty(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _parse_occurred_at(match: re.Match) -> datetime:
    date_value = match["date"]
    time_value = re.sub(r"\s+", " ", match["time"].strip())
    year_format = "%Y" if len(date_value.rsplit("/", 1)[-1]) == 4 else "%y"
    time_format = "%I:%M %p" if re.search(r"[AP]M$", time_value, re.I) else "%H:%M"

    return datetime.strptime(
        f"{date_value} {time_value}",
        f"%d/%m/{year_format} {time_format}",
    ).replace(tzinfo=NAIROBI_TIMEZONE)


def parse_airtel_money_message(message: str) -> ParsedTransactionMessage:
    clean_message = message.strip()
    sent_match = SENT_MONEY_PATTERN.fullmatch(clean_message)

    if sent_match is not None:
        counterparty = _normalize_counterparty(sent_match["counterparty"])
        return ParsedTransactionMessage(
            provider="airtel_money",
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
            network_reference=sent_match["network_reference"].upper(),
        )

    received_match = RECEIVED_MONEY_PATTERN.fullmatch(clean_message)

    if received_match is not None:
        counterparty = _normalize_counterparty(received_match["counterparty"])
        return ParsedTransactionMessage(
            provider="airtel_money",
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
            network_reference=received_match["network_reference"].upper(),
        )

    bundle_match = BUNDLE_PATTERN.fullmatch(clean_message)

    if bundle_match is not None:
        counterparty = _normalize_counterparty(bundle_match["counterparty"])
        return ParsedTransactionMessage(
            provider="airtel_money",
            external_reference=bundle_match["reference"].upper(),
            occurred_at=_parse_occurred_at(bundle_match),
            amount=_parse_money(bundle_match["amount"]),
            currency="KES",
            direction=TransactionDirection.EXPENSE,
            description="Airtel data bundle",
            counterparty=counterparty,
            fee=None,
            resulting_balance=_parse_money(bundle_match["balance"]),
            provider_transaction_type="data_bundle",
        )

    airtime_topup_match = (
        AIRTIME_TOPUP_PATTERN.fullmatch(clean_message)
        or AIRTIME_TOPUP_FOR_LINE_PATTERN.fullmatch(clean_message)
    )

    if airtime_topup_match is not None:
        return ParsedTransactionMessage(
            provider="airtel_money",
            external_reference=airtime_topup_match["reference"].upper(),
            occurred_at=None,
            amount=_parse_money(airtime_topup_match["amount"]),
            currency="KES",
            direction=TransactionDirection.EXPENSE,
            description="Airtel airtime top up",
            counterparty="Airtel subscriber",
            fee=None,
            resulting_balance=_parse_money(airtime_topup_match["balance"]),
            provider_transaction_type="airtime_topup",
        )

    paybill_match = PAYBILL_PATTERN.fullmatch(clean_message)

    if paybill_match is not None:
        counterparty = _normalize_counterparty(paybill_match["counterparty"])
        return ParsedTransactionMessage(
            provider="airtel_money",
            external_reference=paybill_match["reference"].upper(),
            occurred_at=_parse_occurred_at(paybill_match),
            amount=_parse_money(paybill_match["amount"]),
            currency="KES",
            direction=TransactionDirection.EXPENSE,
            description=f"Paid {counterparty}",
            counterparty=counterparty,
            fee=_parse_money(paybill_match["fee"]),
            resulting_balance=_parse_money(paybill_match["balance"]),
            provider_transaction_type="paybill",
            network_reference=paybill_match["network_reference"].upper(),
        )

    raise AirtelMoneyMessageParseError(
        "Unsupported Airtel Money message format."
    )

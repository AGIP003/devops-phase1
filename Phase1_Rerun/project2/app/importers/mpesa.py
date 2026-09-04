import re
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.importers.contracts import (
    ParsedTransactionMessage,
    TransactionDirection,
)


NAIROBI_TIMEZONE = ZoneInfo("Africa/Nairobi")

PHONE_TOKEN = r"(?:\+?254\d{9}|0[\d*]{9})"
OPTIONAL_DAILY_LIMIT = (
    r"(?:\s*Amount you can transact within the day is\s+"
    r"\d[\d,]*(?:\.\d{1,2})?\.)?"
)
OPTIONAL_ONE_APP_LINK = r"(?:\s*Download My OneApp on https?://\S+)?"


SENT_MONEY_PATTERN = re.compile(
    r"^(?P<reference>[A-Z0-9]{10})\s+Confirmed\.\s+"
    r"Ksh(?P<amount>[\d,]+\.\d{2})\s+sent to\s+"
    r"(?!.*\bfor account\b)"
    rf"(?P<counterparty>.+?)\s+{PHONE_TOKEN}\s+on\s+"
    r"(?P<date>\d{1,2}/\d{1,2}/\d{2})\s+at\s+"
    r"(?P<time>\d{1,2}:\d{2}\s+[AP]M)\.?\s+"
    r"New M-PESA balance is Ksh(?P<balance>[\d,]+\.\d{2})\.\s+"
    r"Transaction cost,\s*Ksh(?P<fee>[\d,]+\.\d{2})\."
    + OPTIONAL_DAILY_LIMIT
    + OPTIONAL_ONE_APP_LINK
    + r"$",
    re.IGNORECASE,
)

RECEIVED_MONEY_PATTERN = re.compile(
    r"^(?P<reference>[A-Z0-9]{10})\s+Confirmed\.\s*"
    r"You have received Ksh(?P<amount>[\d,]+\.\d{2})\s+from\s+"
    rf"(?P<counterparty>.+?)\s+{PHONE_TOKEN}\s+on\s+"
    r"(?P<date>\d{1,2}/\d{1,2}/\d{2})\s+at\s+"
    r"(?P<time>\d{1,2}:\d{2}\s+[AP]M)\.?\s+"
    r"New M-PESA balance is Ksh(?P<balance>[\d,]+\.\d{2})\."
    + OPTIONAL_ONE_APP_LINK
    + r"$",
    re.IGNORECASE,
)

BUY_GOODS_PATTERN = re.compile(
    r"^(?P<reference>[A-Z0-9]{10})\s+Confirmed\.\s*"
    r"Ksh\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?)\s+paid to\s+"
    r"(?P<counterparty>.+?)\.\s+on\s+"
    r"(?P<date>\d{1,2}/\d{1,2}/\d{2})\s+at\s+"
    r"(?P<time>\d{1,2}:\d{2}\s*[AP]M)\.?\s*"
    r"New M-PESA balance is Ksh\s*(?P<balance>\d[\d,]*(?:\.\d{1,2})?)\.\s*"
    r"Transaction cost,\s*Ksh\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\."
    + OPTIONAL_DAILY_LIMIT
    + OPTIONAL_ONE_APP_LINK
    + r"$",
    re.IGNORECASE,
)

LOAN_REPAYMENT_PATTERN = re.compile(
    r"^(?P<reference>[A-Z0-9]{10})\s+Confirmed\.\s*"
    r"Your loan repayment of Ksh\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?)\s+"
    r"from your M-PESA account to\s+(?P<counterparty>.+?)\s+on\s+"
    r"(?P<date>\d{1,2}/\d{1,2}/\d{2})\s+at\s+"
    r"(?P<time>\d{1,2}:\d{2}\s*[AP]M)\s+is successful\.\s*"
    r"Your M-PESA balance is Ksh\s*(?P<balance>\d[\d,]*(?:\.\d{1,2})?)\."
    r"$",
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
    r"Transaction cost,\s*Ksh\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\.",
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


def _normalize_counterparty(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_mpesa_message(message: str) -> ParsedTransactionMessage:
    clean_message = message.strip()

    sent_match = SENT_MONEY_PATTERN.fullmatch(clean_message)

    if sent_match is not None:
        counterparty = _normalize_counterparty(sent_match["counterparty"])

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
        counterparty = _normalize_counterparty(received_match["counterparty"])
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

    # Provider promotions change independently of the financial record. Match
    # the stable transaction core and deliberately ignore anything after the
    # reported fee.
    paybill_match = PAYBILL_PATTERN.match(clean_message)

    if paybill_match is not None:
        counterparty = _normalize_counterparty(paybill_match["counterparty"])
        account_reference = paybill_match["account_reference"]
        provider_transaction_type = (
            "data_bundle"
            if re.search(
                r"\bdata\s+bundles?\b",
                f"{counterparty} {account_reference}",
                re.IGNORECASE,
            )
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

    buy_goods_match = BUY_GOODS_PATTERN.fullmatch(clean_message)

    if buy_goods_match is not None:
        counterparty = _normalize_counterparty(buy_goods_match["counterparty"])

        return ParsedTransactionMessage(
            provider="mpesa",
            external_reference=buy_goods_match["reference"].upper(),
            occurred_at=_parse_occurred_at(buy_goods_match),
            amount=_parse_money(buy_goods_match["amount"]),
            currency="KES",
            direction=TransactionDirection.EXPENSE,
            description=f"Paid {counterparty}",
            counterparty=counterparty,
            fee=_parse_money(buy_goods_match["fee"]),
            resulting_balance=_parse_money(buy_goods_match["balance"]),
            provider_transaction_type="buy_goods",
        )

    loan_repayment_match = LOAN_REPAYMENT_PATTERN.fullmatch(clean_message)

    if loan_repayment_match is not None:
        counterparty = _normalize_counterparty(
            loan_repayment_match["counterparty"]
        )

        return ParsedTransactionMessage(
            provider="mpesa",
            external_reference=loan_repayment_match["reference"].upper(),
            occurred_at=_parse_occurred_at(loan_repayment_match),
            amount=_parse_money(loan_repayment_match["amount"]),
            currency="KES",
            direction=TransactionDirection.EXPENSE,
            description=f"{counterparty} loan repayment",
            counterparty=counterparty,
            fee=None,
            resulting_balance=_parse_money(loan_repayment_match["balance"]),
            provider_transaction_type="loan_repayment",
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
        counterparty = _normalize_counterparty(
            withdrawal_match["counterparty"]
        )

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

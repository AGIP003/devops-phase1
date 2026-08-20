import re
from datetime import datetime
from decimal import Decimal

from app.importers.contracts import FulizaNoticeType, ParsedFulizaNotice


FULIZA_DRAW_PATTERN = re.compile(
    r"^(?P<reference>[A-Z0-9]{10})\s+Confirmed\.\s*"
    r"Fuliza M-PESA amount is Ksh\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?)\.\s*"
    r"Access Fee charged Ksh\s*(?P<access_fee>\d[\d,]*(?:\.\d{1,2})?)\.\s*"
    r"Total Fuliza M-PESA outstanding amount is Ksh\s*"
    r"(?P<outstanding>\d[\d,]*(?:\.\d{1,2})?)\s+due on\s+"
    r"(?P<due_date>\d{1,2}/\d{1,2}/\d{2})\."
    r"(?:\s*To check daily charges,.*)?$",
    re.IGNORECASE,
)

FULIZA_REPAYMENT_PATTERN = re.compile(
    r"^(?P<reference>[A-Z0-9]{10})\s+Confirmed\.\s*"
    r"Ksh\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?)\s+from your M-PESA "
    r"has been used to (?P<fully>fully\s+)?pay your outstanding Fuliza M-PESA\.\s*"
    r"Available Fuliza M-PESA limit is Ksh\s*"
    r"(?P<available_limit>\d[\d,]*(?:\.\d{1,2})?)\.\s*"
    r"Your M-PESA balance is\s*(?P<wallet_balance>\d[\d,]*(?:\.\d{1,2})?)\.?$",
    re.IGNORECASE,
)


class FulizaMessageParseError(ValueError):
    pass


def _parse_money(value: str) -> Decimal:
    return Decimal(value.replace(",", ""))


def parse_fuliza_message(message: str) -> ParsedFulizaNotice:
    clean_message = message.strip()
    draw_match = FULIZA_DRAW_PATTERN.fullmatch(clean_message)

    if draw_match is not None:
        return ParsedFulizaNotice(
            provider="fuliza_mpesa",
            external_reference=draw_match["reference"].upper(),
            notice_type=FulizaNoticeType.DRAW,
            amount=_parse_money(draw_match["amount"]),
            currency="KES",
            financing_fee=_parse_money(draw_match["access_fee"]),
            outstanding_amount=_parse_money(draw_match["outstanding"]),
            due_date=datetime.strptime(
                draw_match["due_date"],
                "%d/%m/%y",
            ).date(),
        )

    repayment_match = FULIZA_REPAYMENT_PATTERN.fullmatch(clean_message)

    if repayment_match is not None:
        return ParsedFulizaNotice(
            provider="fuliza_mpesa",
            external_reference=repayment_match["reference"].upper(),
            notice_type=FulizaNoticeType.REPAYMENT,
            amount=_parse_money(repayment_match["amount"]),
            currency="KES",
            settled_in_full=repayment_match["fully"] is not None,
        )

    raise FulizaMessageParseError("Unsupported Fuliza M-PESA message format.")

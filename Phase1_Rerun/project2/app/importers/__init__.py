from app.importers.airtel_money import (
    AirtelMoneyMessageParseError,
    parse_airtel_money_message,
)
from app.importers.contracts import ParsedFulizaNotice, ParsedTransactionMessage
from app.importers.fuliza import FulizaMessageParseError, parse_fuliza_message
from app.importers.mpesa import MpesaMessageParseError, parse_mpesa_message


class UnsupportedFinancialMessageError(ValueError):
    """Raised when none of the deterministic provider parsers recognizes text."""


def parse_financial_message(
    message: str,
) -> ParsedTransactionMessage | ParsedFulizaNotice:
    """Try supported formats without guessing when no full pattern matches."""

    for parser, parse_error in (
        (parse_fuliza_message, FulizaMessageParseError),
        (parse_mpesa_message, MpesaMessageParseError),
        (parse_airtel_money_message, AirtelMoneyMessageParseError),
    ):
        try:
            return parser(message)
        except parse_error:
            continue

    raise UnsupportedFinancialMessageError(
        "This M-Pesa or Airtel Money message format is not supported yet."
    )


__all__ = [
    "ParsedFulizaNotice",
    "ParsedTransactionMessage",
    "UnsupportedFinancialMessageError",
    "parse_financial_message",
]

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from app.importers.airtel_money import (
    AirtelMoneyMessageParseError,
    parse_airtel_money_message,
)
from app.importers.contracts import TransactionDirection


pytestmark = pytest.mark.no_database


NAIROBI_TIMEZONE = ZoneInfo("Africa/Nairobi")


def test_parses_airtel_outgoing_transfer_and_cross_network_reference():
    message = (
        "A3PNEVBMONW. Ksh 15,000 sent to SAMPLE RECIPIENT 700000000 "
        "on 05/08/26 at 10:45 PM. Fee: Ksh 100. Bal: Ksh 4071.5. "
        "MPESA ID: UAAIU1QQ2T"
    )

    result = parse_airtel_money_message(message)

    assert result.provider == "airtel_money"
    assert result.external_reference == "A3PNEVBMONW"
    assert result.network_reference == "UAAIU1QQ2T"
    assert result.amount == Decimal("15000")
    assert result.direction is TransactionDirection.EXPENSE
    assert result.counterparty == "SAMPLE RECIPIENT"
    assert result.fee == Decimal("100")
    assert result.resulting_balance == Decimal("4071.5")
    assert result.occurred_at == datetime(
        2026, 8, 5, 22, 45, tzinfo=NAIROBI_TIMEZONE
    )


def test_parses_airtel_incoming_transfer():
    message = (
        "TID:C3PNETUEDSF. Received Ksh 15,000 from SAMPLE SENDER "
        "254700000000 on 05/08/26 10:43 PM. Bal:Ksh 19171.5 "
        "Sender TID:UAAHD2385T."
    )

    result = parse_airtel_money_message(message)

    assert result.external_reference == "C3PNETUEDSF"
    assert result.network_reference == "UAAHD2385T"
    assert result.direction is TransactionDirection.INCOME
    assert result.description == "Received from SAMPLE SENDER"
    assert result.fee is None
    assert result.resulting_balance == Decimal("19171.5")


def test_parses_airtel_bundle_without_inventing_a_fee():
    message = (
        "B3PPNWQ8431 Confirmed. Bundle purchase successful of Ksh 100 "
        "via Airtel Networks Kenya Ltd on 07/08/26 at 02:09 PM. "
        "Bal: Ksh 3971.5."
    )

    result = parse_airtel_money_message(message)

    assert result.provider_transaction_type == "data_bundle"
    assert result.amount == Decimal("100")
    assert result.description == "Airtel data bundle"
    assert result.counterparty == "Airtel Networks Kenya Ltd"
    assert result.fee is None


def test_parses_airtime_topup_without_retaining_recipient_phone():
    message = (
        "29813220000 Successful. Airtime top up of Ksh 300 "
        "to 0700000000. Bal: Ksh 828.5."
    )

    result = parse_airtel_money_message(message)

    assert result.provider == "airtel_money"
    assert result.external_reference == "29813220000"
    assert result.amount == Decimal("300")
    assert result.direction is TransactionDirection.EXPENSE
    assert result.provider_transaction_type == "airtime_topup"
    assert result.description == "Airtel airtime top up"
    assert result.counterparty == "Airtel subscriber"
    assert result.fee is None
    assert result.resulting_balance == Decimal("828.5")
    assert result.occurred_at is None
    assert "0700000000" not in result.description


def test_parses_airtime_topup_for_line_without_retaining_recipient_line():
    message = (
        "29148245185 Successful. Airtime top up for line 101784609 "
        "of Ksh 20 is successful. Bal: Ksh 520.5. To check your "
        "airtime balance, dial *131#"
    )

    result = parse_airtel_money_message(message)

    assert result.provider == "airtel_money"
    assert result.external_reference == "29148245185"
    assert result.amount == Decimal("20")
    assert result.direction is TransactionDirection.EXPENSE
    assert result.provider_transaction_type == "airtime_topup"
    assert result.description == "Airtel airtime top up"
    assert result.counterparty == "Airtel subscriber"
    assert result.fee is None
    assert result.resulting_balance == Decimal("520.5")
    assert result.occurred_at is None
    assert "101784609" not in result.description
    assert "101784609" not in result.counterparty


def test_parses_airtel_paybill_without_exposing_account_number():
    message = (
        "D3PKHAXK2GW. Ksh 2,284 paid to SAMPLE SUPERMARKET          "
        "account 0000000 on 03/08/2026 19:35. Fee Ksh 0. "
        "Bal:Ksh 4221.5. MPESA ID:UAAAS017X9"
    )

    result = parse_airtel_money_message(message)

    assert result.provider_transaction_type == "paybill"
    assert result.amount == Decimal("2284")
    assert result.counterparty == "SAMPLE SUPERMARKET"
    assert result.description == "Paid SAMPLE SUPERMARKET"
    assert "0000000" not in result.description
    assert result.network_reference == "UAAAS017X9"
    assert result.occurred_at == datetime(
        2026, 8, 3, 19, 35, tzinfo=NAIROBI_TIMEZONE
    )


def test_parses_airtel_paybill_with_colon_after_fee_label():
    message = (
        "X3QE2FJGH6A. Ksh 5,120 paid to SAMPLE BANK C2B account 000000 "
        "on 24/08/2026 14:19.Fee: Ksh 42. Bal:Ksh 658.5. "
        "MPESA ID:UAAAS047TP"
    )

    result = parse_airtel_money_message(message)

    assert result.provider == "airtel_money"
    assert result.provider_transaction_type == "paybill"
    assert result.external_reference == "X3QE2FJGH6A"
    assert result.amount == Decimal("5120")
    assert result.fee == Decimal("42")
    assert result.counterparty == "SAMPLE BANK C2B"
    assert result.description == "Paid SAMPLE BANK C2B"
    assert "000000" not in result.description
    assert result.occurred_at == datetime(
        2026, 8, 24, 14, 19, tzinfo=NAIROBI_TIMEZONE
    )


def test_rejects_unknown_airtel_message():
    with pytest.raises(AirtelMoneyMessageParseError):
        parse_airtel_money_message("Your Airtel balance is available")

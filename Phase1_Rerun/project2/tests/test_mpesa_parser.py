from datetime import datetime
from decimal import Decimal

from app.importers.contracts import TransactionDirection
from app.importers.mpesa import parse_mpesa_message, MpesaMessageParseError
import pytest
from zoneinfo import ZoneInfo


pytestmark = pytest.mark.no_database


NAIROBI_TIMEZONE = ZoneInfo("Africa/Nairobi")

def test_parses_sent_money_message():
    message = (
        "THT7ABC123 Confirmed. Ksh1,250.00 sent to JANE DOE "
        "254700000000 on 20/8/26 at 2:35 PM. "
        "New M-PESA balance is Ksh4,500.25. "
        "Transaction cost, Ksh23.00."
    )

    result = parse_mpesa_message(message)

    assert result.provider == "mpesa"
    assert result.external_reference == "THT7ABC123"
    assert result.amount == Decimal("1250.00")
    assert result.currency == "KES"
    assert result.direction is TransactionDirection.EXPENSE
    assert result.counterparty == "JANE DOE"
    assert result.fee == Decimal("23.00")
    assert result.resulting_balance == Decimal("4500.25")
    assert result.occurred_at == datetime(2026, 8, 20, 14, 35, tzinfo=ZoneInfo("Africa/Nairobi"))

def test_parses_received_money_message():
    message = (
        "THT8DEF456 Confirmed. You have received Ksh2,500.00 "
        "from JOHN DOE 254711111111 on 20/8/26 at 4:05 PM. "
        "New M-PESA balance is Ksh7,000.25."
    )

    result = parse_mpesa_message(message)

    assert result.provider == "mpesa"
    assert result.external_reference == "THT8DEF456"
    assert result.amount == Decimal("2500.00")
    assert result.currency == "KES"
    assert result.direction is TransactionDirection.INCOME
    assert result.counterparty == "JOHN DOE"
    assert result.description == "Received from JOHN DOE"
    assert result.fee is None
    assert result.resulting_balance == Decimal("7000.25")
    assert result.occurred_at == datetime(
        2026,
        8,
        20,
        16,
        5,
        tzinfo=ZoneInfo("Africa/Nairobi"),
    )

def test_rejects_non_mpesa_message():
    with pytest.raises(MpesaMessageParseError):
        parse_mpesa_message("250 lunch")


def test_parses_paybill_message_without_exposing_account_number():
    message = (
        "UAAIU33DWG Confirmed. Ksh1,000.00 sent to NCBA BANK KENYA PLC. "
        "for account 0000000000 on 17/8/26 at 8:02 PM "
        "New M-PESA balance is Ksh0.00. Transaction cost, Ksh10.00."
        "Amount you can transact within the day is 498,830.00. "
        "Download My OneApp on https://saf.cx/example"
    )

    result = parse_mpesa_message(message)

    assert result.external_reference == "UAAIU33DWG"
    assert result.amount == Decimal("1000.00")
    assert result.direction is TransactionDirection.EXPENSE
    assert result.counterparty == "NCBA BANK KENYA PLC"
    assert result.description == "Paid NCBA BANK KENYA PLC"
    assert "0000000000" not in result.description
    assert result.fee == Decimal("10.00")
    assert result.resulting_balance == Decimal("0.00")


def test_parses_data_bundle_as_paybill_message():
    message = (
        "UAAIU3A99A Confirmed. Ksh25.00 sent to SAFARICOM DATA BUNDLES "
        "for account SAFARICOM DATA BUNDLES on 19/8/26 at 4:49 PM "
        "New M-PESA balance is Ksh0.00. Transaction cost, Ksh0.00."
        "Amount you can transact within the day is 499,975.00. "
        "Download My OneApp on https://saf.cx/example"
    )

    result = parse_mpesa_message(message)

    assert result.amount == Decimal("25.00")
    assert result.counterparty == "SAFARICOM DATA BUNDLES"
    assert result.description == "Paid SAFARICOM DATA BUNDLES"
    assert result.provider_transaction_type == "data_bundle"
    assert result.fee == Decimal("0.00")


def test_parses_airtime_purchase_message():
    message = (
        "UAAIU30XE9 confirmed.You bought Ksh50.00 of airtime "
        "on 17/8/26 at 10:23 AM.New M-PESA balance is Ksh6.11. "
        "Transaction cost, Ksh0.00. Amount you can transact within the day "
        "is 499,950.00. Download My OneApp on https://saf.cx/example"
    )

    result = parse_mpesa_message(message)

    assert result.external_reference == "UAAIU30XE9"
    assert result.amount == Decimal("50.00")
    assert result.direction is TransactionDirection.EXPENSE
    assert result.description == "Safaricom airtime"
    assert result.counterparty == "Safaricom"
    assert result.fee == Decimal("0.00")
    assert result.resulting_balance == Decimal("6.11")


def test_parses_withdrawal_as_transfer_without_exposing_agent_number():
    message = (
        "UAAIU1WURT Confirmed.on 7/8/26 at 2:19 PMWithdraw Ksh100.00 "
        "from 000000 - SAMPLE AGENT New M-PESA balance is Ksh315.11. "
        "Transaction cost, Ksh11.00. Amount you can transact within the "
        "day is 499,900.00. Get a Lipa Na M-PESA Till online: "
        "https://m-pesaforbusiness.co.ke/"
    )

    result = parse_mpesa_message(message)

    assert result.amount == Decimal("100.00")
    assert result.direction is TransactionDirection.TRANSFER
    assert result.provider_transaction_type == "withdrawal"
    assert result.counterparty == "SAMPLE AGENT"
    assert "000000" not in result.description
    assert result.fee == Decimal("11.00")
    assert result.resulting_balance == Decimal("315.11")


def test_parses_kcb_mpesa_loan_repayment_as_expense():
    message = (
        "UAAIU1QRKT Confirmed. Your loan repayment of Ksh12,345.00 from "
        "your M-PESA account to KCB M-PESA on 5/8/26 at 10:48 PM is "
        "successful. Your M-PESA balance is Ksh800.00."
    )

    result = parse_mpesa_message(message)

    assert result.amount == Decimal("12345.00")
    assert result.direction is TransactionDirection.EXPENSE
    assert result.provider_transaction_type == "loan_repayment"
    assert result.counterparty == "KCB M-PESA"
    assert result.description == "KCB M-PESA loan repayment"


def test_parses_received_money_with_masked_phone_and_ignores_link():
    message = (
        "UAAIU1PBBA Confirmed.You have received Ksh3,000.00 from "
        "SAMPLE SENDER 0100***000 on 4/8/26 at 12:24 PM "
        "New M-PESA balance is Ksh3,000.00. "
        "Download My OneApp on https://saf.cx/example"
    )

    result = parse_mpesa_message(message)

    assert result.direction is TransactionDirection.INCOME
    assert result.counterparty == "SAMPLE SENDER"
    assert "0100" not in result.description
    assert result.provider_transaction_type == "received_money"


def test_parses_sent_money_with_optional_daily_limit_and_link():
    message = (
        "UAAIU1HD8Q Confirmed. Ksh50.00 sent to SAMPLE PERSON 0117000000 "
        "on 3/8/26 at 7:52 PM. New M-PESA balance is Ksh0.00. "
        "Transaction cost, Ksh0.00. Amount you can transact within the "
        "day is 499,950.00. Download My OneApp on https://saf.cx/example"
    )

    result = parse_mpesa_message(message)

    assert result.direction is TransactionDirection.EXPENSE
    assert result.counterparty == "SAMPLE PERSON"
    assert "0117000000" not in result.description
    assert result.provider_transaction_type == "send_money"


def test_parses_buy_goods_without_exposing_till_or_phone():
    message = (
        "UAAIU1RQ41 Confirmed. Ksh100.00 paid to SAMPLE MERCHANT LTD. "
        "on 6/8/26 at 10:46 AM.New M-PESA balance is Ksh475.11. "
        "Transaction cost, Ksh0.00. Amount you can transact within the "
        "day is 499,900.00. Download My OneApp on https://saf.cx/example"
    )

    result = parse_mpesa_message(message)

    assert result.amount == Decimal("100.00")
    assert result.direction is TransactionDirection.EXPENSE
    assert result.counterparty == "SAMPLE MERCHANT LTD"
    assert result.description == "Paid SAMPLE MERCHANT LTD"
    assert result.provider_transaction_type == "buy_goods"


def test_paybill_ignores_changing_provider_promotion_after_financial_core():
    message = (
        "UI1IU4R9BT Confirmed. Ksh20.00 sent to SAFARICOM POSTPAID "
        "BUNDLES for account SAFARICOM DATA BUNDLES on 1/9/26 at "
        "9:21 AM New M-PESA balance is Ksh0.00. Transaction cost, "
        "Ksh0.00. See all your balances now https://saf.cx/example"
    )

    result = parse_mpesa_message(message)

    assert result.external_reference == "UI1IU4R9BT"
    assert result.amount == Decimal("20.00")
    assert result.fee == Decimal("0.00")
    assert result.counterparty == "SAFARICOM POSTPAID BUNDLES"
    assert result.provider_transaction_type == "data_bundle"
    assert "SAFARICOM DATA BUNDLES" not in result.description
    assert "saf.cx" not in result.description

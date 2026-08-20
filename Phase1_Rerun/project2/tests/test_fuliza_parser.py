from datetime import date
from decimal import Decimal

import pytest

from app.importers.contracts import FulizaNoticeType
from app.importers.fuliza import FulizaMessageParseError, parse_fuliza_message


def test_parses_fuliza_draw_without_treating_it_as_income():
    message = (
        "UAAIU33DWG Confirmed. Fuliza M-PESA amount is Ksh 1010.00. "
        "Access Fee charged Ksh 10.10. Total Fuliza M-PESA outstanding "
        "amount is Ksh1135.13 due on 16/09/26. To check daily charges, "
        "Dial *334#OK Select Query Charges"
    )

    result = parse_fuliza_message(message)

    assert result.provider == "fuliza_mpesa"
    assert result.external_reference == "UAAIU33DWG"
    assert result.notice_type is FulizaNoticeType.DRAW
    assert result.amount == Decimal("1010.00")
    assert result.financing_fee == Decimal("10.10")
    assert result.daily_maintenance_fee is None
    assert result.outstanding_amount == Decimal("1135.13")
    assert result.due_date == date(2026, 9, 16)


def test_parses_fuliza_full_repayment():
    message = (
        "UAAIU1QT2Z Confirmed. Ksh 1089.89 from your M-PESA has been used "
        "to fully pay your outstanding Fuliza M-PESA. Available Fuliza "
        "M-PESA limit is Ksh 3100.00. Your M-PESA balance is 13910.11."
    )

    result = parse_fuliza_message(message)

    assert result.notice_type is FulizaNoticeType.REPAYMENT
    assert result.amount == Decimal("1089.89")
    assert result.settled_in_full is True


def test_rejects_unknown_fuliza_message():
    with pytest.raises(FulizaMessageParseError):
        parse_fuliza_message("Fuliza balance requested")

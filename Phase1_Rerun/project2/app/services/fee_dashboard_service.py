"""Owner-scoped fee reporting and versioned public tariff references."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from sqlalchemy import func, select

from app.extensions import db
from app.models.category import Category
from app.models.provider_financing_event import ProviderFinancingEvent
from app.models.transaction import Transaction
from app.models.transaction_import import TransactionImport


ZERO = Decimal("0")
MONEY = Decimal("0.01")
TARIFF_CATALOG_VERSION = "kenya-public-tariffs-2026-08-23"

AIRTEL_SOURCE = "https://www.airtelkenya.com/tariffs_charges"
AIRTEL_PAYBILL_SOURCE = (
    "https://airtelkenya.com/"
    "Airtel-Money-Reduces-Its-Paybill-And-Wallet-To-Bank-Charges"
)
MPESA_SOURCE = "https://www.safaricom.co.ke/images/Downloads/mpesa-business-till.pdf"


class FeeEstimateError(ValueError):
    pass


def _money(value) -> str:
    return format(Decimal(value or ZERO).quantize(MONEY, rounding=ROUND_HALF_UP), "f")


def _band_table(rows):
    return [
        {"upTo": str(upper), "fee": str(fee)}
        for upper, fee in rows
    ]


AIRTEL_OTHER_NETWORK = (
    (Decimal("100"), Decimal("0")),
    (Decimal("500"), Decimal("6")),
    (Decimal("1000"), Decimal("11")),
    (Decimal("1500"), Decimal("20")),
    (Decimal("2500"), Decimal("30")),
    (Decimal("3500"), Decimal("50")),
    (Decimal("5000"), Decimal("50")),
    (Decimal("7500"), Decimal("70")),
    (Decimal("10000"), Decimal("80")),
    (Decimal("15000"), Decimal("90")),
    (Decimal("25000"), Decimal("95")),
    (Decimal("35000"), Decimal("100")),
    (Decimal("50000"), Decimal("105")),
    (Decimal("250000"), Decimal("105")),
)

AIRTEL_WITHDRAWAL = (
    (Decimal("49"), Decimal("0")),
    (Decimal("100"), Decimal("10")),
    (Decimal("500"), Decimal("25")),
    (Decimal("1000"), Decimal("25")),
    (Decimal("1500"), Decimal("25")),
    (Decimal("2500"), Decimal("25")),
    (Decimal("3500"), Decimal("44")),
    (Decimal("5000"), Decimal("55")),
    (Decimal("7500"), Decimal("70")),
    (Decimal("10000"), Decimal("95")),
    (Decimal("15000"), Decimal("135")),
    (Decimal("20000"), Decimal("150")),
    (Decimal("35000"), Decimal("160")),
    (Decimal("40000"), Decimal("240")),
    (Decimal("45000"), Decimal("260")),
    (Decimal("50000"), Decimal("270")),
    (Decimal("250000"), Decimal("300")),
)

AIRTEL_PAYBILL = (
    (Decimal("100"), Decimal("0")),
    (Decimal("500"), Decimal("4")),
    (Decimal("1000"), Decimal("9")),
    (Decimal("1500"), Decimal("12")),
    (Decimal("2500"), Decimal("13")),
    (Decimal("3500"), Decimal("20")),
    (Decimal("5000"), Decimal("20")),
    (Decimal("7500"), Decimal("33")),
    (Decimal("10000"), Decimal("37")),
    (Decimal("15000"), Decimal("57")),
    (Decimal("20000"), Decimal("62")),
    (Decimal("25000"), Decimal("67")),
    (Decimal("30000"), Decimal("72")),
    (Decimal("35000"), Decimal("95")),
    (Decimal("40000"), Decimal("99")),
    (Decimal("45000"), Decimal("103")),
    (Decimal("250000"), Decimal("105")),
)


TARIFF_SERVICES = {
    ("airtel_money", "on_net"): {
        "provider": "airtel_money",
        "service": "on_net",
        "name": "Airtel to Airtel",
        "helper": "Published as free across all bands.",
        "source": AIRTEL_SOURCE,
        "sourceLabel": "Airtel Money current tariff guide",
        "effectiveLabel": "Current page checked 23 Aug 2026",
        "bands": ((Decimal("250000"), Decimal("0")),),
    },
    ("airtel_money", "other_network"): {
        "provider": "airtel_money",
        "service": "other_network",
        "name": "Airtel to another network",
        "helper": "Use this when the recipient is not on Airtel.",
        "source": AIRTEL_SOURCE,
        "sourceLabel": "Airtel Money current tariff guide",
        "effectiveLabel": "Current page checked 23 Aug 2026",
        "bands": AIRTEL_OTHER_NETWORK,
    },
    ("airtel_money", "withdrawal"): {
        "provider": "airtel_money",
        "service": "withdrawal",
        "name": "Airtel agent withdrawal",
        "helper": "Published customer withdrawal charge.",
        "source": AIRTEL_SOURCE,
        "sourceLabel": "Airtel Money current tariff guide",
        "effectiveLabel": "Current page checked 23 Aug 2026",
        "bands": AIRTEL_WITHDRAWAL,
    },
    ("airtel_money", "paybill_wallet_bank"): {
        "provider": "airtel_money",
        "service": "paybill_wallet_bank",
        "name": "Airtel Paybill / wallet to bank",
        "helper": "Official revised Paybill and wallet-to-bank bands.",
        "source": AIRTEL_PAYBILL_SOURCE,
        "sourceLabel": "Airtel revised Paybill and wallet-to-bank charges",
        "effectiveLabel": "Published 2 Nov 2023; verify before relying on it",
        "bands": AIRTEL_PAYBILL,
    },
    ("mpesa", "buy_goods"): {
        "provider": "mpesa",
        "service": "buy_goods",
        "name": "M-PESA Buy Goods",
        "helper": "Standard customer charge is zero; fuel stations are excluded.",
        "source": MPESA_SOURCE,
        "sourceLabel": "Safaricom Lipa na M-PESA business material",
        "effectiveLabel": "Public rule checked 23 Aug 2026",
        "bands": ((Decimal("250000"), Decimal("0")),),
    },
}


def get_fee_tariff_catalog() -> dict[str, object]:
    services = []
    for tariff in TARIFF_SERVICES.values():
        services.append({
            key: value
            for key, value in tariff.items()
            if key != "bands"
        } | {"bands": _band_table(tariff["bands"])})
    return {
        "version": TARIFF_CATALOG_VERSION,
        "currency": "KES",
        "services": services,
        "bankReferences": [
            {
                "name": "KCB Bank Kenya",
                "sourceLabel": "Tariff guide effective April 2026",
                "source": "https://ke.kcbgroup.com/our-tariffs",
                "note": "Charges depend on account, channel and transaction type.",
            },
            {
                "name": "Equity Bank Kenya",
                "sourceLabel": "Official products and services tariff guide",
                "source": "https://equitygroupholdings.com/ke/images/docs/tariff-guide.pdf",
                "note": "Use the exact channel row and confirm taxes before recording a fee.",
            },
        ],
        "warning": (
            "Tariffs can change. Estimates are planning aids; provider messages "
            "and bank statements remain stronger evidence."
        ),
    }


def estimate_public_tariff(provider: str, service: str, amount) -> dict[str, object]:
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise FeeEstimateError("Amount must be a number") from error
    if not value.is_finite() or value <= ZERO:
        raise FeeEstimateError("Amount must be greater than zero")
    if value != value.quantize(MONEY):
        raise FeeEstimateError("Amount cannot have more than 2 decimal places")

    tariff = TARIFF_SERVICES.get((provider, service))
    if tariff is None:
        raise FeeEstimateError("That provider and service combination is unsupported")
    for upper, fee in tariff["bands"]:
        if value <= upper:
            return {
                "provider": provider,
                "service": service,
                "serviceName": tariff["name"],
                "amount": _money(value),
                "estimatedFee": _money(fee),
                "source": tariff["source"],
                "sourceLabel": tariff["sourceLabel"],
                "effectiveLabel": tariff["effectiveLabel"],
                "catalogVersion": TARIFF_CATALOG_VERSION,
                "confidence": "published_band_estimate",
                "warning": (
                    "Estimate only. Confirm the final charge in the provider "
                    "message or statement."
                ),
            }
    raise FeeEstimateError("Amount is outside the published tariff range")


def build_fee_dashboard(user_id: int, *, today: date | None = None) -> dict[str, object]:
    current = today or date.today()
    month_start = current.replace(day=1)
    week_start = current - timedelta(days=current.weekday())
    fee_total = func.coalesce(func.sum(TransactionImport.fee), ZERO)
    rows = db.session.execute(
        select(
            TransactionImport.provider,
            TransactionImport.fee_source,
            fee_total,
            func.count(TransactionImport.id),
        )
        .join(Transaction, TransactionImport.transaction_id == Transaction.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.date.between(month_start, current),
            TransactionImport.fee.is_not(None),
        )
        .group_by(TransactionImport.provider, TransactionImport.fee_source)
    )

    providers: dict[str, dict[str, object]] = {}
    confirmed = estimated = ZERO
    for provider, source, total, count in rows:
        amount = Decimal(total)
        values = providers.setdefault(provider, {"total": ZERO, "count": 0})
        values["total"] += amount
        values["count"] += int(count)
        if source == "estimated_tariff":
            estimated += amount
        else:
            confirmed += amount

    financing_amount = (
        func.coalesce(ProviderFinancingEvent.financing_fee, ZERO)
        + func.coalesce(ProviderFinancingEvent.daily_maintenance_fee, ZERO)
    )
    financing_month = Decimal(db.session.scalar(
        select(func.coalesce(func.sum(financing_amount), ZERO)).where(
            ProviderFinancingEvent.user_id == user_id,
            ProviderFinancingEvent.recorded_on.between(month_start, current),
        )
    ) or ZERO)
    if financing_month:
        providers["fuliza_mpesa"] = {
            "total": financing_month,
            "count": int(db.session.scalar(
                select(func.count(ProviderFinancingEvent.id)).where(
                    ProviderFinancingEvent.user_id == user_id,
                    ProviderFinancingEvent.recorded_on.between(month_start, current),
                    financing_amount > ZERO,
                )
            ) or 0),
        }
        confirmed += financing_month

    weekly_imports = Decimal(db.session.scalar(
        select(fee_total)
        .select_from(TransactionImport)
        .join(Transaction, TransactionImport.transaction_id == Transaction.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.date.between(week_start, current),
            TransactionImport.fee.is_not(None),
        )
    ) or ZERO)
    weekly_financing = Decimal(db.session.scalar(
        select(func.coalesce(func.sum(financing_amount), ZERO)).where(
            ProviderFinancingEvent.user_id == user_id,
            ProviderFinancingEvent.recorded_on.between(week_start, current),
        )
    ) or ZERO)

    unknown_count = int(db.session.scalar(
        select(func.count(TransactionImport.id))
        .join(Transaction, TransactionImport.transaction_id == Transaction.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.date.between(month_start, current),
            TransactionImport.fee.is_(None),
            TransactionImport.fee_source == "unknown",
        )
    ) or 0)

    expense_total = Decimal(db.session.scalar(
        select(func.coalesce(func.sum(Transaction.amount), ZERO))
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Category.type == "expense",
            Transaction.date.between(month_start, current),
        )
    ) or ZERO)
    month_total = confirmed + estimated

    imported_events = db.session.execute(
        select(TransactionImport, Transaction)
        .join(Transaction, TransactionImport.transaction_id == Transaction.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            TransactionImport.fee.is_not(None),
        )
        .order_by(Transaction.date.desc(), TransactionImport.id.desc())
        .limit(8)
    )
    recent = [{
        "id": f"transaction-{record.id}",
        "provider": record.provider,
        "description": transaction.merchant_name or transaction.description,
        "date": transaction.date.isoformat(),
        "amount": _money(transaction.amount),
        "fee": _money(record.fee),
        "source": record.fee_source,
    } for record, transaction in imported_events]

    financing_events = db.session.scalars(
        select(ProviderFinancingEvent)
        .where(
            ProviderFinancingEvent.user_id == user_id,
            financing_amount > ZERO,
        )
        .order_by(ProviderFinancingEvent.recorded_on.desc())
        .limit(8)
    )
    recent.extend({
        "id": f"financing-{event.id}",
        "provider": event.provider,
        "description": f"Fuliza {event.event_type} charge",
        "date": event.recorded_on.isoformat(),
        "amount": _money(event.principal_amount),
        "fee": _money(
            Decimal(event.financing_fee or ZERO)
            + Decimal(event.daily_maintenance_fee or ZERO)
        ),
        "source": "provider_reported",
    } for event in financing_events)
    recent.sort(key=lambda item: (item["date"], item["id"]), reverse=True)

    provider_totals = [{
        "provider": provider,
        "total": _money(values["total"]),
        "count": values["count"],
    } for provider, values in providers.items()]
    provider_totals.sort(key=lambda item: Decimal(item["total"]), reverse=True)

    outflows = expense_total + month_total
    return {
        "period": {
            "monthStart": month_start.isoformat(),
            "weekStart": week_start.isoformat(),
            "end": current.isoformat(),
            "currency": "KES",
        },
        "totalWeek": _money(weekly_imports + weekly_financing),
        "totalMonth": _money(month_total),
        "confirmedMonth": _money(confirmed),
        "estimatedMonth": _money(estimated),
        "unknownFeeCount": unknown_count,
        "feeShareOfOutflows": (
            _money((month_total / outflows) * Decimal("100"))
            if outflows > ZERO
            else None
        ),
        "providerTotals": provider_totals,
        "recentEvents": recent[:8],
        "catalogVersion": TARIFF_CATALOG_VERSION,
    }

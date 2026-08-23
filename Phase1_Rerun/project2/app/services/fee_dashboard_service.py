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
TARIFF_CATALOG_VERSION = "kenya-public-tariffs-2026-08-23.3"

AIRTEL_SOURCE = "https://www.airtelkenya.com/tariffs_charges"
AIRTEL_PAYBILL_SOURCE = (
    "https://airtelkenya.com/"
    "Airtel-Money-Reduces-Its-Paybill-And-Wallet-To-Bank-Charges"
)
MPESA_SOURCE = "https://www.safaricom.co.ke/images/Downloads/mpesa-business-till.pdf"
MPESA_TARIFF_SOURCE = (
    "https://www.safaricom.co.ke/images/Downloads/"
    "M-PESA-BULK-PAYMENT-TARIFF-FORM.pdf"
)
MPESA_POCHI_SOURCE = (
    "https://www.safaricom.co.ke/media-center-landing/press-releases/"
    "m-pesa-tariff-reduction"
)
FULIZA_SOURCE = (
    "https://www.safaricom.co.ke/media-center-landing/press-releases/"
    "safaricom-ncba-and-kcb-restructure-fuliza-with-free-daily-fees"
)


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

MPESA_SEND_MONEY = (
    (Decimal("100"), Decimal("0")),
    (Decimal("500"), Decimal("7")),
    (Decimal("1000"), Decimal("13")),
    (Decimal("1500"), Decimal("23")),
    (Decimal("2500"), Decimal("33")),
    (Decimal("3500"), Decimal("53")),
    (Decimal("5000"), Decimal("57")),
    (Decimal("7500"), Decimal("78")),
    (Decimal("10000"), Decimal("90")),
    (Decimal("15000"), Decimal("100")),
    (Decimal("20000"), Decimal("105")),
    (Decimal("250000"), Decimal("108")),
)

MPESA_WITHDRAWAL = (
    (Decimal("49"), Decimal("0")),
    (Decimal("100"), Decimal("11")),
    (Decimal("500"), Decimal("29")),
    (Decimal("1000"), Decimal("29")),
    (Decimal("1500"), Decimal("29")),
    (Decimal("2500"), Decimal("29")),
    (Decimal("3500"), Decimal("52")),
    (Decimal("5000"), Decimal("69")),
    (Decimal("7500"), Decimal("87")),
    (Decimal("10000"), Decimal("115")),
    (Decimal("15000"), Decimal("167")),
    (Decimal("20000"), Decimal("185")),
    (Decimal("35000"), Decimal("197")),
    (Decimal("50000"), Decimal("278")),
    (Decimal("250000"), Decimal("309")),
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
    ("mpesa", "send_money"): {
        "provider": "mpesa",
        "service": "send_money",
        "name": "M-PESA Send Money",
        "helper": (
            "Estimate from Safaricom's registered-wallet bands, then replace "
            "it with the confirmation-message fee when available."
        ),
        "source": MPESA_TARIFF_SOURCE,
        "sourceLabel": "Safaricom M-PESA registered-wallet tariff form",
        "effectiveLabel": "Public Safaricom form checked 23 Aug 2026",
        "bands": MPESA_SEND_MONEY,
    },
    ("mpesa", "withdrawal"): {
        "provider": "mpesa",
        "service": "withdrawal",
        "name": "M-PESA agent withdrawal",
        "helper": (
            "Estimate the standard withdrawal band; the confirmation message "
            "remains the final charge."
        ),
        "source": MPESA_TARIFF_SOURCE,
        "sourceLabel": "Safaricom M-PESA withdrawal tariff form",
        "effectiveLabel": "Public Safaricom form checked 23 Aug 2026",
        "bands": MPESA_WITHDRAWAL,
    },
    ("mpesa", "pochi"): {
        "provider": "mpesa",
        "service": "pochi",
        "name": "M-PESA Pochi la Biashara",
        "helper": (
            "Safaricom applies Send Money bands to Pochi; confirm the charge "
            "shown before completing the transaction."
        ),
        "source": MPESA_POCHI_SOURCE,
        "sourceLabel": "Safaricom M-PESA tariff announcement",
        "effectiveLabel": "Planning estimate using the current Send Money bands",
        "bands": MPESA_SEND_MONEY,
    },
}


MONITORED_SERVICES = (
    {
        "provider": "mpesa",
        "service": "paybill",
        "name": "M-PESA Paybill",
        "helper": "Paybill charges can depend on the business tariff arrangement.",
        "source": "https://www.safaricom.co.ke/media-center-landing/frequently-asked-questions/m-pesa-paybill",
        "sourceLabel": "Safaricom M-PESA Paybill guide",
        "effectiveLabel": "Use the charge in the confirmation message",
    },
    {
        "provider": "fuliza_mpesa",
        "service": "access_fee",
        "name": "Fuliza access fee",
        "helper": "Captured separately from the amount borrowed.",
        "source": FULIZA_SOURCE,
        "sourceLabel": "Safaricom Fuliza pricing announcement",
        "effectiveLabel": "Your Fuliza message is the authoritative charge",
    },
    {
        "provider": "fuliza_mpesa",
        "service": "maintenance_fee",
        "name": "Fuliza daily maintenance fee",
        "helper": "Monitor recurring maintenance charges without treating principal as spending.",
        "source": FULIZA_SOURCE,
        "sourceLabel": "Safaricom Fuliza pricing announcement",
        "effectiveLabel": "Terms vary by amount and borrowing duration",
    },
    {
        "provider": "bank",
        "service": "transfer",
        "name": "Bank transfer",
        "helper": "Monitor the actual charge from the selected bank and transfer channel.",
        "source": "https://www.centralbank.go.ke/bank-supervision/",
        "sourceLabel": "Central Bank of Kenya banking supervision",
        "effectiveLabel": "Fees vary by bank, account and channel",
    },
    {
        "provider": "bank",
        "service": "atm_withdrawal",
        "name": "Bank ATM withdrawal",
        "helper": "Own-bank and other-bank ATM charges can differ.",
        "source": "https://www.centralbank.go.ke/bank-supervision/",
        "sourceLabel": "Central Bank of Kenya banking supervision",
        "effectiveLabel": "Use the bank statement or tariff for the account",
    },
    {
        "provider": "bank",
        "service": "card_charge",
        "name": "Bank card or foreign-currency charge",
        "helper": "Monitor card, conversion and cross-border charges as separate costs.",
        "source": "https://www.centralbank.go.ke/bank-supervision/",
        "sourceLabel": "Central Bank of Kenya banking supervision",
        "effectiveLabel": "Charges depend on bank, card, currency and merchant channel",
    },
)


def get_fee_tariff_catalog() -> dict[str, object]:
    services = []
    for tariff in TARIFF_SERVICES.values():
        services.append({
            key: value
            for key, value in tariff.items()
            if key != "bands"
        } | {
            "bands": _band_table(tariff["bands"]),
            "estimationAvailable": True,
        })
    services.extend({
        **service,
        "bands": [],
        "estimationAvailable": False,
    } for service in MONITORED_SERVICES)
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
            {
                "name": "Co-operative Bank of Kenya",
                "sourceLabel": "Official Co-op Bank tariff guide",
                "source": "https://www.co-opbank.co.ke/tariff-guide",
                "note": "Mobile, agent, ATM and PesaLink channels have different charges.",
            },
            {
                "name": "NCBA Bank Kenya",
                "sourceLabel": "Official NCBA tariffs and fees",
                "source": "https://ncbagroup.com/ke/tariffs-fees/",
                "note": "Choose the account and transaction channel before using a tariff row.",
            },
            {
                "name": "Absa Bank Kenya",
                "sourceLabel": "Official Absa rates and fees",
                "source": "https://www.absabank.co.ke/rates-and-fees/",
                "note": "Bank-to-wallet and account tariffs are published separately.",
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

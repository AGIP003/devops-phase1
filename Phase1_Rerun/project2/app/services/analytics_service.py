"""Database-backed personal-finance analytics.

The service deliberately keeps actual cash flow separate from planned or
future commitments. Combining them would double-count bills once their payment
also appears as a transaction.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import case, func, or_, select

from app.extensions import db
from app.models.budget import Budget, BudgetItem
from app.models.category import Category
from app.models.debt import Debt, DebtEntry, DebtSchedule
from app.models.recurring_commitment import RecurringCommitment
from app.models.savings_goal import SavingsGoal, SavingsGoalEntry
from app.models.transaction import Transaction
from app.models.transaction_import import TransactionImport
from app.models.provider_financing_event import ProviderFinancingEvent


ZERO = Decimal("0")
MONEY = Decimal("0.01")
SUPPORTED_PERIODS = {"30-days", "90-days", "6-months", "12-months", "all"}
SUPPORTED_TREND_PERIODS = {"week", "month", "year", "all"}


class AnalyticsPeriodError(ValueError):
    """Raised when an unsupported analytics period is requested."""


class AnalyticsSearchError(ValueError):
    """Raised when an analytics lookup cannot be safely executed."""


def _money(value: Decimal | int | None) -> str:
    return format(Decimal(value or ZERO).quantize(MONEY, rounding=ROUND_HALF_UP), "f")


def _percentage(numerator: Decimal, denominator: Decimal) -> str | None:
    if denominator <= ZERO:
        return None
    return format(
        ((numerator / denominator) * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ),
        "f",
    )


def _subtract_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 - months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    return date(year, month, min(value.day, monthrange(year, month)[1]))


def resolve_period(period: str, *, today: date | None = None) -> tuple[date | None, date]:
    """Return an inclusive date range for a supported period key."""
    if period not in SUPPORTED_PERIODS:
        raise AnalyticsPeriodError(
            f"Unsupported period '{period}'. Choose one of: "
            + ", ".join(sorted(SUPPORTED_PERIODS))
        )

    end = today or date.today()
    if period == "all":
        return None, end
    if period == "30-days":
        return end - timedelta(days=29), end
    if period == "90-days":
        return end - timedelta(days=89), end
    if period == "6-months":
        return _subtract_months(end, 6) + timedelta(days=1), end
    return _subtract_months(end, 12) + timedelta(days=1), end


def _dated(statement, column, start: date | None, end: date):
    statement = statement.where(column <= end)
    return statement.where(column >= start) if start is not None else statement


def _transaction_aggregates(user_id: int, start: date | None, end: date):
    base_filters = (
        Transaction.user_id == user_id,
        Transaction.deleted_at.is_(None),
    )

    totals_statement = (
        select(Category.type, func.coalesce(func.sum(Transaction.amount), ZERO))
        .select_from(Transaction)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(*base_filters)
        .group_by(Category.type)
    )
    totals_statement = _dated(totals_statement, Transaction.date, start, end)
    totals_by_type = {
        transaction_type: Decimal(total)
        for transaction_type, total in db.session.execute(totals_statement)
    }

    monthly_statement = (
        select(
            func.date_trunc("month", Transaction.date).label("month"),
            Category.type,
            func.coalesce(func.sum(Transaction.amount), ZERO),
        )
        .select_from(Transaction)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(*base_filters)
        .group_by("month", Category.type)
        .order_by("month")
    )
    monthly_statement = _dated(monthly_statement, Transaction.date, start, end)
    monthly: dict[str, dict[str, Decimal]] = {}
    for month, transaction_type, total in db.session.execute(monthly_statement):
        key = month.date().isoformat()[:7]
        values = monthly.setdefault(key, {"income": ZERO, "expense": ZERO})
        if transaction_type in values:
            values[transaction_type] = Decimal(total)

    category_statement = (
        select(
            func.coalesce(Category.name, "Uncategorized"),
            func.coalesce(func.sum(Transaction.amount), ZERO),
            func.count(Transaction.id),
        )
        .select_from(Transaction)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(*base_filters, Category.type == "expense")
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )
    category_statement = _dated(category_statement, Transaction.date, start, end)
    categories = [
        {
            "category": name,
            "amount": _money(total),
            "transactionCount": count,
        }
        for name, total, count in db.session.execute(category_statement)
    ]

    daily_statement = (
        select(
            Transaction.date,
            func.coalesce(
                func.sum(case((Category.type == "income", Transaction.amount), else_=ZERO)),
                ZERO,
            ),
            func.coalesce(
                func.sum(case((Category.type == "expense", Transaction.amount), else_=ZERO)),
                ZERO,
            ),
            func.count(Transaction.id),
        )
        .select_from(Transaction)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(*base_filters)
        .group_by(Transaction.date)
        .order_by(Transaction.date)
    )
    daily_statement = _dated(daily_statement, Transaction.date, start, end)
    daily = [
        {
            "date": occurred_on.isoformat(),
            "income": _money(income),
            "expenses": _money(expenses),
            "transactionCount": count,
        }
        for occurred_on, income, expenses, count in db.session.execute(daily_statement)
    ]

    return totals_by_type, monthly, categories, daily


def resolve_trend_period(
    period: str,
    *,
    anchor: date | None = None,
    offset: int = 0,
    all_time_start: date | None = None,
) -> tuple[date, date, str]:
    """Resolve a calendar-aligned period and chart grain.

    ``offset=-1`` means the previous complete calendar period. This is not the
    same as a rolling 30-day window, so the distinction stays in the API.
    """
    if period not in SUPPORTED_TREND_PERIODS:
        raise AnalyticsPeriodError(
            "Unsupported trend period. Choose one of: week, month, year, all"
        )
    if offset > 0 or offset < -120:
        raise AnalyticsPeriodError("Trend offset must be between -120 and 0")
    if period == "all":
        if offset != 0:
            raise AnalyticsPeriodError("All-time analytics cannot use an offset")
        end = anchor or date.today()
        return all_time_start or end, end, "month"

    current = anchor or date.today()
    if period == "week":
        current += timedelta(weeks=offset)
        start = current - timedelta(days=current.weekday())
        return start, start + timedelta(days=6), "day"
    if period == "month":
        current = _subtract_months(current, -offset)
        start = current.replace(day=1)
        return start, date(
            current.year,
            current.month,
            monthrange(current.year, current.month)[1],
        ), "day"
    year = current.year + offset
    return date(year, 1, 1), date(year, 12, 31), "month"


def build_transaction_coverage(user_id: int) -> dict[str, object]:
    """Describe the owned, active history available for honest conclusions."""
    first, last, count, active_days = db.session.execute(
        select(
            func.min(Transaction.date),
            func.max(Transaction.date),
            func.count(Transaction.id),
            func.count(func.distinct(Transaction.date)),
        ).where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
        )
    ).one()
    return {
        "firstTransactionDate": first.isoformat() if first else None,
        "lastTransactionDate": last.isoformat() if last else None,
        "transactionCount": int(count),
        "activeDays": int(active_days),
    }


def _coverage_for_period(
    coverage: dict[str, object],
    start: date,
    end: date,
) -> dict[str, object]:
    first_text = coverage["firstTransactionDate"]
    last_text = coverage["lastTransactionDate"]
    if not first_text or not last_text:
        status = "no_records"
        overlaps = False
    else:
        first = date.fromisoformat(str(first_text))
        last = date.fromisoformat(str(last_text))
        overlaps = first <= end and last >= start
        status = "covered" if overlaps else (
            "before_history" if end < first else "after_history"
        )
    return {**coverage, "requestedPeriodStatus": status, "hasRecordedOverlap": overlaps}


def _expense_dimension_breakdown(
    user_id: int,
    start: date | None,
    end: date,
    column,
    label: str,
    *,
    limit: int = 5,
) -> list[dict[str, object]]:
    """Group free text consistently without merging semantically different text."""
    normalized = func.lower(
        func.regexp_replace(func.trim(column), r"\s+", " ", "g")
    )
    statement = (
        select(
            func.min(column),
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.amount), ZERO),
            func.min(Transaction.date),
            func.max(Transaction.date),
        )
        .select_from(Transaction)
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Category.type == "expense",
            column.is_not(None),
            func.trim(column) != "",
        )
        .group_by(normalized)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
    )
    statement = _dated(statement, Transaction.date, start, end)
    return [
        {
            label: value,
            "count": int(count),
            "amount": _money(amount),
            "firstDate": first.isoformat(),
            "lastDate": last.isoformat(),
        }
        for value, count, amount, first, last in db.session.execute(statement)
    ]


def _clean_search_query(query: str) -> str:
    if not isinstance(query, str):
        raise AnalyticsSearchError("Search query must be text")
    clean = " ".join(query.strip().split())
    if len(clean) < 2:
        raise AnalyticsSearchError("Search query must contain at least 2 characters")
    if len(clean) > 100:
        raise AnalyticsSearchError("Search query cannot exceed 100 characters")
    return clean


def _month_keys(start: date, end: date):
    current = start.replace(day=1)
    while current <= end:
        yield current
        current = (
            date(current.year + 1, 1, 1)
            if current.month == 12
            else date(current.year, current.month + 1, 1)
        )


def build_description_trend(
    user_id: int,
    query: str,
    period: str,
    *,
    anchor: date | None = None,
    offset: int = 0,
):
    """Aggregate owned expense matches without exposing raw transaction rows."""
    clean_query = _clean_search_query(query)
    coverage = build_transaction_coverage(user_id)
    first_date = (
        date.fromisoformat(str(coverage["firstTransactionDate"]))
        if coverage["firstTransactionDate"]
        else None
    )
    start, end, grain = resolve_trend_period(
        period,
        anchor=anchor,
        offset=offset,
        all_time_start=first_date,
    )
    search_pattern = f"%{clean_query}%"
    bucket = (
        func.date_trunc("month", Transaction.date)
        if grain == "month"
        else Transaction.date
    )
    statement = (
        select(
            bucket.label("bucket"),
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.amount), ZERO),
        )
        .select_from(Transaction)
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Category.type == "expense",
            Transaction.date.between(start, end),
            or_(
                func.coalesce(Transaction.description, "").ilike(search_pattern),
                func.coalesce(Transaction.merchant_name, "").ilike(search_pattern),
                func.coalesce(Category.name, "").ilike(search_pattern),
            ),
        )
        .group_by(bucket)
        .order_by(bucket)
    )

    rows = {}
    total_count = 0
    total_amount = ZERO
    for bucket_value, count, amount in db.session.execute(statement):
        bucket_date = (
            bucket_value.date()
            if hasattr(bucket_value, "date")
            else bucket_value
        )
        rows[bucket_date] = (int(count), Decimal(amount))
        total_count += int(count)
        total_amount += Decimal(amount)

    keys = (
        _month_keys(start, end)
        if grain == "month"
        else (start + timedelta(days=offset) for offset in range((end - start).days + 1))
    )
    series = []
    for key in keys:
        count, amount = rows.get(key, (0, ZERO))
        series.append({
            "bucket": key.isoformat()[:7] if grain == "month" else key.isoformat(),
            "count": count,
            "amount": _money(amount),
        })

    match_filters = (
        Transaction.user_id == user_id,
        Transaction.deleted_at.is_(None),
        Category.type == "expense",
        Transaction.date.between(start, end),
        or_(
            func.coalesce(Transaction.description, "").ilike(search_pattern),
            func.coalesce(Transaction.merchant_name, "").ilike(search_pattern),
            func.coalesce(Category.name, "").ilike(search_pattern),
        ),
    )

    def grouped_matches(column, label: str):
        normalized = func.lower(
            func.regexp_replace(func.trim(column), r"\s+", " ", "g")
        )
        grouped = (
            select(
                func.min(column),
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.amount), ZERO),
                func.min(Transaction.date),
                func.max(Transaction.date),
            )
            .select_from(Transaction)
            .join(Category, Transaction.category_id == Category.id)
            .where(*match_filters, column.is_not(None), func.trim(column) != "")
            .group_by(normalized)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(5)
        )
        return [
            {
                label: value,
                "count": int(count),
                "amount": _money(amount),
                "firstDate": first.isoformat(),
                "lastDate": last.isoformat(),
            }
            for value, count, amount, first, last in db.session.execute(grouped)
        ]

    return {
        "query": clean_query,
        "period": {
            "key": period,
            "offset": offset,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "grain": grain,
            "currency": "KES",
        },
        "totalCount": total_count,
        "totalAmount": _money(total_amount),
        "topDescriptions": grouped_matches(Transaction.description, "description"),
        "topMerchants": grouped_matches(Transaction.merchant_name, "merchant"),
        "topCategories": grouped_matches(Category.name, "category"),
        "recordedHistory": _coverage_for_period(coverage, start, end),
        "series": series,
    }


def _proactive_transaction_insights(
    user_id: int,
    start: date | None,
    end: date,
    *,
    categories: list[dict[str, object]],
    recorded_expenses: Decimal,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Calculate explainable signals; none of these rules changes user data."""
    descriptions = _expense_dimension_breakdown(
        user_id, start, end, Transaction.description, "description"
    )
    merchants = _expense_dimension_breakdown(
        user_id, start, end, Transaction.merchant_name, "merchant"
    )

    small_threshold = Decimal("500.00")
    small_statement = select(
        func.count(Transaction.id),
        func.coalesce(func.sum(Transaction.amount), ZERO),
    ).select_from(Transaction).join(
        Category, Transaction.category_id == Category.id
    ).where(
        Transaction.user_id == user_id,
        Transaction.deleted_at.is_(None),
        Category.type == "expense",
        Transaction.amount <= small_threshold,
    )
    small_statement = _dated(small_statement, Transaction.date, start, end)
    small_count, small_total = db.session.execute(small_statement).one()
    small_total = Decimal(small_total)

    weekday_statement = (
        select(
            func.extract("isodow", Transaction.date),
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.amount), ZERO),
        )
        .select_from(Transaction)
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Category.type == "expense",
        )
        .group_by(func.extract("isodow", Transaction.date))
        .order_by(func.sum(Transaction.amount).desc())
    )
    weekday_statement = _dated(weekday_statement, Transaction.date, start, end)
    weekday_names = {
        1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
        5: "Friday", 6: "Saturday", 7: "Sunday",
    }
    rhythms = [
        {"day": weekday_names[int(day)], "count": int(count), "amount": _money(amount)}
        for day, count, amount in db.session.execute(weekday_statement)
    ]

    repeated_label = func.coalesce(
        func.nullif(func.trim(Transaction.merchant_name), ""),
        func.nullif(func.trim(Transaction.description), ""),
    )
    normalized_label = func.lower(
        func.regexp_replace(repeated_label, r"\s+", " ", "g")
    )
    recurring_statement = (
        select(
            func.min(repeated_label),
            func.count(Transaction.id),
            func.count(func.distinct(Transaction.date)),
            func.coalesce(func.sum(Transaction.amount), ZERO),
            func.coalesce(func.avg(Transaction.amount), ZERO),
        )
        .select_from(Transaction)
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Category.type == "expense",
            repeated_label.is_not(None),
        )
        .group_by(normalized_label)
        .having(
            func.count(Transaction.id) >= 3,
            func.count(func.distinct(Transaction.date)) >= 2,
        )
        .order_by(func.sum(Transaction.amount).desc())
        .limit(3)
    )
    recurring_statement = _dated(recurring_statement, Transaction.date, start, end)
    recurring_candidates = [
        {
            "label": value,
            "count": int(count),
            "activeDays": int(active_days),
            "amount": _money(amount),
            "averageAmount": _money(average),
        }
        for value, count, active_days, amount, average in db.session.execute(
            recurring_statement
        )
    ]

    baseline_statement = (
        select(
            func.count(Transaction.id),
            func.coalesce(func.avg(Transaction.amount), ZERO),
        )
        .select_from(Transaction)
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Category.type == "expense",
            Transaction.date <= end,
        )
    )
    baseline_count, baseline_average = db.session.execute(baseline_statement).one()
    largest_statement = (
        select(
            Transaction.amount,
            Transaction.description,
            Transaction.merchant_name,
            Transaction.date,
        )
        .select_from(Transaction)
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Category.type == "expense",
        )
        .order_by(Transaction.amount.desc())
        .limit(1)
    )
    largest_statement = _dated(largest_statement, Transaction.date, start, end)
    largest = db.session.execute(largest_statement).one_or_none()

    insights: list[dict[str, object]] = []
    if int(small_count) >= 3 and small_total > ZERO:
        insights.append({
            "type": "small_spend_pattern",
            "severity": "medium",
            "title": "Small purchases added up",
            "metric": _money(small_total),
            "supporting": f"{int(small_count)} purchases of KES {_money(small_threshold)} or less",
            "comparison": (
                f"{_percentage(small_total, recorded_expenses)}% of recorded spending"
                if recorded_expenses > ZERO else "No spending-share comparison available"
            ),
            "caveat": "The KES 500 threshold is a review aid, not a judgement about necessity.",
            "query": None,
        })
    if recurring_candidates:
        candidate = recurring_candidates[0]
        insights.append({
            "type": "recurring_candidate",
            "severity": "medium",
            "title": f"{candidate['label']} appears repeatedly",
            "metric": f"{candidate['count']} times",
            "supporting": f"KES {candidate['amount']} in total across {candidate['activeDays']} days",
            "comparison": f"Average recorded amount: KES {candidate['averageAmount']}",
            "caveat": "Repeated wording is a clue, not proof that this is a subscription or bill.",
            "query": candidate["label"],
        })
    baseline_average = Decimal(baseline_average)
    if (
        largest
        and int(baseline_count) >= 5
        and baseline_average > ZERO
        and Decimal(largest.amount) >= baseline_average * Decimal("2")
    ):
        label = largest.merchant_name or largest.description or "One purchase"
        insights.append({
            "type": "unusual_purchase",
            "severity": "medium",
            "title": f"{label} was higher than your usual purchase",
            "metric": _money(largest.amount),
            "supporting": f"Recorded on {largest.date.isoformat()}",
            "comparison": f"Your all-time average recorded purchase is KES {_money(baseline_average)}",
            "caveat": "A large amount can be intentional; review the record before drawing a conclusion.",
            "query": label,
        })
    if rhythms and int(rhythms[0]["count"]) >= 2:
        leading_day = rhythms[0]
        insights.append({
            "type": "spending_rhythm",
            "severity": "low",
            "title": f"{leading_day['day']} carried the most spending",
            "metric": _money(Decimal(leading_day["amount"])),
            "supporting": f"Across {leading_day['count']} recorded purchases",
            "comparison": "Highest weekday total in the selected period",
            "caveat": "This describes recorded history; it does not predict future spending.",
            "query": None,
        })

    details = {
        "topDescriptions": descriptions,
        "topMerchants": merchants,
        "smallPurchaseThreshold": _money(small_threshold),
        "smallPurchaseCount": int(small_count),
        "smallPurchaseTotal": _money(small_total),
        "weekdayTotals": rhythms,
        "recurringCandidates": recurring_candidates,
        "historicalAveragePurchase": _money(baseline_average),
        "historicalPurchaseCount": int(baseline_count),
    }
    return insights, details


def _provider_fee_summary(user_id: int, start: date | None, end: date):
    transaction_statement = (
        select(
            TransactionImport.fee_source,
            func.coalesce(func.sum(TransactionImport.fee), ZERO),
        )
        .select_from(TransactionImport)
        .join(Transaction, TransactionImport.transaction_id == Transaction.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            TransactionImport.fee.is_not(None),
        )
        .group_by(TransactionImport.fee_source)
    )
    transaction_statement = _dated(
        transaction_statement,
        Transaction.date,
        start,
        end,
    )
    by_source = {
        source: Decimal(amount)
        for source, amount in db.session.execute(transaction_statement)
    }

    financing_fee = func.coalesce(ProviderFinancingEvent.financing_fee, ZERO)
    maintenance_fee = func.coalesce(
        ProviderFinancingEvent.daily_maintenance_fee,
        ZERO,
    )
    financing_statement = select(
        func.coalesce(func.sum(financing_fee + maintenance_fee), ZERO)
    ).where(
        ProviderFinancingEvent.user_id == user_id,
        ProviderFinancingEvent.currency_code == "KES",
    )
    financing_statement = _dated(
        financing_statement,
        ProviderFinancingEvent.recorded_on,
        start,
        end,
    )
    financing_total = Decimal(db.session.scalar(financing_statement) or ZERO)

    provider_reported = by_source.get("provider_reported", ZERO)
    user_confirmed = by_source.get("user_confirmed", ZERO)
    estimated = by_source.get("estimated_tariff", ZERO)
    confirmed = provider_reported + user_confirmed + financing_total
    return {
        "providerReported": provider_reported,
        "userConfirmed": user_confirmed,
        "estimated": estimated,
        "financingCharges": financing_total,
        "confirmed": confirmed,
        "total": confirmed + estimated,
    }


def _provider_fee_timeline(user_id: int, start: date | None, end: date):
    """Return fee totals by month and day for reconciled charts."""
    monthly: dict[str, Decimal] = {}
    daily: dict[str, Decimal] = {}

    for grain, target in (("month", monthly), ("day", daily)):
        bucket = (
            func.date_trunc("month", Transaction.date)
            if grain == "month"
            else Transaction.date
        )
        statement = (
            select(
                bucket,
                func.coalesce(func.sum(TransactionImport.fee), ZERO),
            )
            .select_from(TransactionImport)
            .join(Transaction, TransactionImport.transaction_id == Transaction.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.deleted_at.is_(None),
                TransactionImport.fee.is_not(None),
            )
            .group_by(bucket)
        )
        statement = _dated(statement, Transaction.date, start, end)
        for bucket_value, amount in db.session.execute(statement):
            bucket_date = (
                bucket_value.date()
                if hasattr(bucket_value, "date")
                else bucket_value
            )
            key = (
                bucket_date.isoformat()[:7]
                if grain == "month"
                else bucket_date.isoformat()
            )
            target[key] = target.get(key, ZERO) + Decimal(amount)

        financing_bucket = (
            func.date_trunc("month", ProviderFinancingEvent.recorded_on)
            if grain == "month"
            else ProviderFinancingEvent.recorded_on
        )
        financing_amount = (
            func.coalesce(ProviderFinancingEvent.financing_fee, ZERO)
            + func.coalesce(
                ProviderFinancingEvent.daily_maintenance_fee,
                ZERO,
            )
        )
        financing_statement = (
            select(
                financing_bucket,
                func.coalesce(func.sum(financing_amount), ZERO),
            )
            .where(
                ProviderFinancingEvent.user_id == user_id,
                ProviderFinancingEvent.currency_code == "KES",
            )
            .group_by(financing_bucket)
        )
        financing_statement = _dated(
            financing_statement,
            ProviderFinancingEvent.recorded_on,
            start,
            end,
        )
        for bucket_value, amount in db.session.execute(financing_statement):
            bucket_date = (
                bucket_value.date()
                if hasattr(bucket_value, "date")
                else bucket_value
            )
            key = (
                bucket_date.isoformat()[:7]
                if grain == "month"
                else bucket_date.isoformat()
            )
            target[key] = target.get(key, ZERO) + Decimal(amount)

    return monthly, daily


def build_calendar_cashflow(
    user_id: int,
    period: str,
    *,
    anchor: date | None = None,
    offset: int = 0,
):
    """Build a compact calendar-aligned cash-flow snapshot for AI tools."""
    coverage = build_transaction_coverage(user_id)
    first_date = (
        date.fromisoformat(str(coverage["firstTransactionDate"]))
        if coverage["firstTransactionDate"]
        else None
    )
    start, end, _ = resolve_trend_period(
        period,
        anchor=anchor,
        offset=offset,
        all_time_start=first_date,
    )
    totals, _, categories, daily = _transaction_aggregates(user_id, start, end)
    income = totals.get("income", ZERO)
    spending = totals.get("expense", ZERO)
    fees = _provider_fee_summary(user_id, start, end)
    expenses = spending + fees["total"]
    top_descriptions = _expense_dimension_breakdown(
        user_id, start, end, Transaction.description, "description", limit=3
    )
    top_merchants = _expense_dimension_breakdown(
        user_id, start, end, Transaction.merchant_name, "merchant", limit=3
    )
    return {
        "period": {
            "key": period,
            "offset": offset,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "currency": "KES",
        },
        "income": _money(income),
        "recordedExpenses": _money(spending),
        "confirmedFees": _money(fees["confirmed"]),
        "estimatedFees": _money(fees["estimated"]),
        "totalExpenses": _money(expenses),
        "net": _money(income - expenses),
        "transactionCount": sum(
            item["transactionCount"] for item in daily
        ),
        "topExpenseCategories": categories[:5],
        "topDescriptions": top_descriptions,
        "topMerchants": top_merchants,
        "recordedHistory": _coverage_for_period(coverage, start, end),
    }


def _monthly_equivalent(amount: Decimal, frequency: str, custom_days: int | None) -> Decimal:
    factors = {
        "weekly": Decimal("52") / Decimal("12"),
        "monthly": Decimal("1"),
        "quarterly": Decimal("1") / Decimal("3"),
        "termly": Decimal("3") / Decimal("12"),
        "yearly": Decimal("1") / Decimal("12"),
    }
    if frequency == "custom" and custom_days:
        return amount * (Decimal("365.2425") / Decimal(custom_days)) / Decimal("12")
    return amount * factors.get(frequency, Decimal("0"))


def _commitment_summary(user_id: int):
    statement = select(
        RecurringCommitment.kind,
        RecurringCommitment.amount,
        RecurringCommitment.frequency,
        RecurringCommitment.custom_interval_days,
        RecurringCommitment.currency_code,
    ).where(
        RecurringCommitment.user_id == user_id,
        RecurringCommitment.status == "active",
        RecurringCommitment.deleted_at.is_(None),
    )

    totals = {"bill": ZERO, "subscription": ZERO}
    unsupported_currencies: set[str] = set()
    for kind, amount, frequency, custom_days, currency in db.session.execute(statement):
        if currency != "KES":
            unsupported_currencies.add(currency)
            continue
        totals[kind] += _monthly_equivalent(Decimal(amount), frequency, custom_days)
    return totals, sorted(unsupported_currencies)


def _budget_summary(user_id: int):
    planned = db.session.scalar(
        select(func.coalesce(func.sum(Budget.target_amount), ZERO)).where(
            Budget.user_id == user_id
        )
    )
    actual = db.session.scalar(
        select(func.coalesce(func.sum(BudgetItem.actual_amount), ZERO))
        .select_from(BudgetItem)
        .join(Budget, BudgetItem.budget_id == Budget.id)
        .where(Budget.user_id == user_id)
    )
    planned_value, actual_value = Decimal(planned), Decimal(actual)
    return {
        "planned": _money(planned_value),
        "spent": _money(actual_value),
        "remaining": _money(planned_value - actual_value),
        "usedPercentage": _percentage(actual_value, planned_value),
    }


def _debt_summary(user_id: int, start: date | None, end: date):
    entry_delta = case(
        (DebtEntry.entry_type.in_(("interest", "fee", "adjustment_increase")), DebtEntry.amount),
        (DebtEntry.entry_type.in_(("repayment", "adjustment_decrease")), -DebtEntry.amount),
        else_=ZERO,
    )
    # Sum per-debt balances in Python to avoid multiplying opening balances by entries.
    balance_rows = db.session.execute(
        select(
            Debt.opening_balance,
            func.coalesce(func.sum(entry_delta), ZERO),
        )
        .select_from(Debt)
        .outerjoin(DebtEntry, DebtEntry.debt_id == Debt.id)
        .where(Debt.user_id == user_id, Debt.status == "active", Debt.deleted_at.is_(None))
        .group_by(Debt.id, Debt.opening_balance)
    )
    current_balance = sum(
        (max(Decimal(opening) + Decimal(delta), ZERO) for opening, delta in balance_rows),
        ZERO,
    )

    entry_statement = (
        select(
            DebtEntry.entry_type,
            func.coalesce(func.sum(DebtEntry.amount), ZERO),
        )
        .select_from(DebtEntry)
        .join(Debt, DebtEntry.debt_id == Debt.id)
        .where(Debt.user_id == user_id, Debt.deleted_at.is_(None))
        .group_by(DebtEntry.entry_type)
    )
    entry_statement = _dated(entry_statement, DebtEntry.occurred_on, start, end)
    entries = {kind: Decimal(total) for kind, total in db.session.execute(entry_statement)}

    schedule_rows = db.session.execute(
        select(
            DebtSchedule.installment_amount,
            DebtSchedule.frequency,
            DebtSchedule.interval_count,
        )
        .select_from(DebtSchedule)
        .join(Debt, DebtSchedule.debt_id == Debt.id)
        .where(
            Debt.user_id == user_id,
            Debt.status == "active",
            Debt.deleted_at.is_(None),
        )
    )
    scheduled = ZERO
    schedule_factors = {
        "daily": Decimal("365.2425") / Decimal("12"),
        "weekly": Decimal("52") / Decimal("12"),
        "monthly": Decimal("1"),
    }
    for amount, frequency, interval_count in schedule_rows:
        if amount is None or frequency == "one_time":
            continue
        scheduled += (
            Decimal(amount)
            * schedule_factors[frequency]
            / Decimal(interval_count)
        )
    return {
        "activeBalance": _money(current_balance),
        "periodRepayments": _money(entries.get("repayment", ZERO)),
        "periodFees": _money(entries.get("fee", ZERO)),
        "monthlyScheduledPayments": _money(scheduled),
    }


def _goal_summary(user_id: int, today: date):
    statement = (
        select(
            SavingsGoal.id,
            SavingsGoal.target_amount,
            SavingsGoal.target_date,
            SavingsGoal.currency_code,
            func.coalesce(
                func.sum(
                    case(
                        (SavingsGoalEntry.entry_type == "contribution", SavingsGoalEntry.amount),
                        else_=-SavingsGoalEntry.amount,
                    )
                ),
                ZERO,
            ),
        )
        .outerjoin(SavingsGoalEntry, SavingsGoalEntry.goal_id == SavingsGoal.id)
        .where(SavingsGoal.user_id == user_id, SavingsGoal.deleted_at.is_(None))
        .group_by(SavingsGoal.id)
    )

    target = current = required_monthly = ZERO
    unsupported_currencies: set[str] = set()
    count = 0
    for _, goal_target, target_date, currency, saved in db.session.execute(statement):
        if currency != "KES":
            unsupported_currencies.add(currency)
            continue
        count += 1
        goal_target, saved = Decimal(goal_target), max(Decimal(saved), ZERO)
        target += goal_target
        current += saved
        remaining = max(goal_target - saved, ZERO)
        months_left = max(
            Decimal("1"),
            Decimal(max((target_date - today).days, 0)) / Decimal("30.4375"),
        )
        required_monthly += remaining / months_left

    return {
        "activeCount": count,
        "target": _money(target),
        "saved": _money(current),
        "remaining": _money(max(target - current, ZERO)),
        "progressPercentage": _percentage(current, target),
        "requiredMonthlyContribution": _money(required_monthly),
    }, sorted(unsupported_currencies)


def _upcoming(user_id: int, today: date):
    commitment_rows = db.session.execute(
        select(
            RecurringCommitment.id,
            RecurringCommitment.kind,
            RecurringCommitment.name,
            RecurringCommitment.amount,
            RecurringCommitment.next_due_date,
        )
        .where(
            RecurringCommitment.user_id == user_id,
            RecurringCommitment.status == "active",
            RecurringCommitment.deleted_at.is_(None),
            RecurringCommitment.next_due_date >= today,
            RecurringCommitment.currency_code == "KES",
        )
        .order_by(RecurringCommitment.next_due_date)
        .limit(8)
    )
    debt_rows = db.session.execute(
        select(Debt.id, Debt.title, DebtSchedule.installment_amount, DebtSchedule.next_due_date)
        .join(DebtSchedule, DebtSchedule.debt_id == Debt.id)
        .where(
            Debt.user_id == user_id,
            Debt.status == "active",
            Debt.deleted_at.is_(None),
            DebtSchedule.next_due_date >= today,
            Debt.currency_code == "KES",
        )
        .order_by(DebtSchedule.next_due_date)
        .limit(8)
    )
    items = [
        {"id": identifier, "kind": kind, "name": name, "amount": _money(amount), "dueDate": due.isoformat()}
        for identifier, kind, name, amount, due in commitment_rows
    ]
    items.extend(
        {"id": identifier, "kind": "debt", "name": name, "amount": _money(amount), "dueDate": due.isoformat()}
        for identifier, name, amount, due in debt_rows
        if amount is not None
    )
    return sorted(items, key=lambda item: item["dueDate"])[:8]


def build_analytics_summary(user_id: int, period: str, *, today: date | None = None):
    """Build a user-owned analytics read model using database aggregates."""
    current_date = today or date.today()
    start, end = resolve_period(period, today=current_date)
    totals, monthly, categories, daily = _transaction_aggregates(user_id, start, end)
    income = totals.get("income", ZERO)
    recorded_expenses = totals.get("expense", ZERO)
    fees = _provider_fee_summary(user_id, start, end)
    monthly_fees, daily_fees = _provider_fee_timeline(user_id, start, end)
    transaction_fees = fees["total"]
    expenses = recorded_expenses + transaction_fees
    debt = _debt_summary(user_id, start, end)
    debt_fees = Decimal(debt["periodFees"])
    net = income - expenses

    for month, amount in monthly_fees.items():
        values = monthly.setdefault(
            month,
            {"income": ZERO, "expense": ZERO},
        )
        values["fees"] = amount
    for values in monthly.values():
        values.setdefault("fees", ZERO)

    for item in daily:
        fee_amount = daily_fees.get(item["date"], ZERO)
        item["fees"] = _money(fee_amount)
        item["expenses"] = _money(
            Decimal(item["expenses"]) + fee_amount
        )

    commitments, commitment_currencies = _commitment_summary(user_id)
    goals, goal_currencies = _goal_summary(user_id, current_date)
    monthly_committed = (
        commitments["bill"]
        + commitments["subscription"]
        + Decimal(debt["monthlyScheduledPayments"])
        + Decimal(goals["requiredMonthlyContribution"])
    )
    if start is not None:
        effective_start = start
    elif monthly:
        year, month = (int(part) for part in next(iter(monthly)).split("-"))
        effective_start = date(year, month, 1)
    else:
        effective_start = end
    period_days = max((end - effective_start).days + 1, 1)
    monthly_income = income * Decimal("30.4375") / Decimal(period_days)

    opportunities = []
    if categories and recorded_expenses > ZERO:
        leading = categories[0]
        share = Decimal(leading["amount"]) / recorded_expenses
        if share >= Decimal("0.30"):
            opportunities.append({
                "type": "category_concentration",
                "severity": "medium",
                "title": f"Review {leading['category']} spending",
                "explanation": f"It represents {_percentage(Decimal(leading['amount']), recorded_expenses)}% of recorded purchases in this period.",
                "potentialMonthlyAdjustment": None,
            })
    if debt_fees > ZERO:
        opportunities.append({
            "type": "debt_fees",
            "severity": "high",
            "title": "Review recorded debt fees",
            "explanation": f"KES {_money(debt_fees)} in debt fees was recorded during this period.",
            "potentialMonthlyAdjustment": None,
        })
    commitment_ratio = _percentage(monthly_committed, monthly_income)
    if commitment_ratio is not None and Decimal(commitment_ratio) >= Decimal("60"):
        opportunities.append({
            "type": "commitment_pressure",
            "severity": "high",
            "title": "Monthly commitments are high",
            "explanation": f"Planned commitments use about {commitment_ratio}% of average monthly income.",
            "potentialMonthlyAdjustment": None,
        })

    transaction_insights, expense_details = _proactive_transaction_insights(
        user_id,
        start,
        end,
        categories=categories,
        recorded_expenses=recorded_expenses,
    )
    opportunities.extend(transaction_insights)

    if start is not None and categories:
        previous_end = start - timedelta(days=1)
        previous_start = previous_end - (end - start)
        previous_category_statement = (
            select(
                func.coalesce(Category.name, "Uncategorized"),
                func.coalesce(func.sum(Transaction.amount), ZERO),
            )
            .select_from(Transaction)
            .outerjoin(Category, Transaction.category_id == Category.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.deleted_at.is_(None),
                Category.type == "expense",
                Transaction.date.between(previous_start, previous_end),
            )
            .group_by(Category.name)
        )
        previous_categories = {
            name: Decimal(amount)
            for name, amount in db.session.execute(previous_category_statement)
        }
        drivers = [
            {
                "category": item["category"],
                "current": Decimal(item["amount"]),
                "previous": previous_categories.get(item["category"], ZERO),
            }
            for item in categories
        ]
        leading_driver = max(
            drivers,
            key=lambda item: item["current"] - item["previous"],
        )
        driver_change = leading_driver["current"] - leading_driver["previous"]
        if driver_change > ZERO:
            opportunities.append({
                "type": "change_driver",
                "severity": "medium",
                "title": f"{leading_driver['category']} drove the spending increase",
                "metric": _money(driver_change),
                "supporting": f"KES {_money(leading_driver['current'])} in this period",
                "comparison": f"KES {_money(leading_driver['previous'])} in the previous equal-length period",
                "caveat": "The comparison uses recorded transactions from equal-length windows.",
                "query": leading_driver["category"],
            })

    if goals["activeCount"] and Decimal(goals["requiredMonthlyContribution"]) > ZERO:
        required = Decimal(goals["requiredMonthlyContribution"])
        other_commitments = max(monthly_committed - required, ZERO)
        available = max(monthly_income - other_commitments, ZERO)
        if available < required:
            opportunities.append({
                "type": "goal_pressure",
                "severity": "high",
                "title": "Recorded cash flow may not cover planned goal contributions",
                "metric": _money(required - available),
                "supporting": f"KES {goals['requiredMonthlyContribution']} is required monthly across active goals",
                "comparison": f"KES {_money(available)} remains after other monthly commitments",
                "caveat": "This estimate depends on complete income records and current target dates.",
                "query": None,
            })

    upcoming = _upcoming(user_id, current_date)
    upcoming_30_days = [
        item for item in upcoming
        if date.fromisoformat(item["dueDate"]) <= current_date + timedelta(days=30)
    ]
    upcoming_total = sum(
        (Decimal(item["amount"]) for item in upcoming_30_days), ZERO
    )
    if len(upcoming_30_days) >= 2:
        opportunities.append({
            "type": "upcoming_pressure",
            "severity": "medium",
            "title": "Several payments are due within 30 days",
            "metric": _money(upcoming_total),
            "supporting": f"{len(upcoming_30_days)} recorded bills, subscriptions or debt payments",
            "comparison": "Due over the next 30 days",
            "caveat": "Due dates and planned amounts may change before payment.",
            "query": None,
        })

    warnings = []
    unsupported = sorted(set(commitment_currencies + goal_currencies))
    if unsupported:
        warnings.append(
            "Commitments or goals in unsupported currencies were excluded: "
            + ", ".join(unsupported)
        )
    if fees["estimated"] > ZERO:
        warnings.append(
            "Total expenses include KES "
            f"{_money(fees['estimated'])} in clearly labelled estimated "
            "provider fees. Review or confirm them before relying on the total."
        )

    return {
        "period": {
            "key": period,
            "start": start.isoformat() if start else None,
            "end": end.isoformat(),
            "currency": "KES",
        },
        "cashFlow": {
            "income": _money(income),
            "recordedExpenses": _money(recorded_expenses),
            "expenses": _money(expenses),
            "transactionFees": _money(transaction_fees),
            "confirmedTransactionFees": _money(fees["confirmed"]),
            "estimatedTransactionFees": _money(fees["estimated"]),
            "financingCharges": _money(fees["financingCharges"]),
            "net": _money(net),
            "savingsRate": _percentage(net, income),
        },
        "commitments": {
            "monthlyBills": _money(commitments["bill"]),
            "monthlySubscriptions": _money(commitments["subscription"]),
            "monthlyDebtPayments": debt["monthlyScheduledPayments"],
            "monthlyGoalContributions": goals["requiredMonthlyContribution"],
            "totalMonthlyCommitted": _money(monthly_committed),
            "committedIncomePercentage": commitment_ratio,
        },
        "budget": _budget_summary(user_id),
        "debts": debt,
        "goals": goals,
        "monthlyTrend": [
            {
                "month": month,
                "income": _money(values["income"]),
                "recordedExpenses": _money(values["expense"]),
                "fees": _money(values["fees"]),
                "expenses": _money(values["expense"] + values["fees"]),
                "net": _money(
                    values["income"] - values["expense"] - values["fees"]
                ),
            }
            for month, values in sorted(monthly.items())
        ],
        "expenseCategories": categories,
        "expenseDetails": expense_details,
        "dailyActivity": daily,
        "upcoming": upcoming,
        "adjustmentOpportunities": opportunities,
        "recordedHistory": build_transaction_coverage(user_id),
        "coverage": {
            "transactions": True,
            "budgets": True,
            "goals": True,
            "debts": True,
            "bills": True,
            "subscriptions": True,
            "transactionFees": True,
            "debtFees": True,
        },
        "warnings": warnings,
    }

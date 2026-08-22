from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.schemas import AnalyticsQuestionPlan, AnalyticsToolName
from app.services.analytics_service import (
    build_analytics_summary,
    build_calendar_cashflow,
    build_description_trend,
    resolve_trend_period,
)


def _previous_anchor(period: str, anchor: date) -> date:
    start, _, _ = resolve_trend_period(period, anchor=anchor)
    return start - timedelta(days=1)


def execute_analytics_tool(
    user_id: int,
    plan: AnalyticsQuestionPlan,
    *,
    today: date | None = None,
) -> dict[str, object]:
    """Execute one allow-listed, ownership-filtered analytics operation."""
    anchor = today or date.today()

    if plan.tool == AnalyticsToolName.SEARCH_SPENDING:
        return build_description_trend(
            user_id,
            plan.query or "",
            plan.period,
            anchor=anchor,
        )

    if plan.tool == AnalyticsToolName.CASHFLOW_SUMMARY:
        return build_calendar_cashflow(user_id, plan.period, anchor=anchor)

    if plan.tool == AnalyticsToolName.FEE_SUMMARY:
        snapshot = build_calendar_cashflow(user_id, plan.period, anchor=anchor)
        return {
            "period": snapshot["period"],
            "confirmedFees": snapshot["confirmedFees"],
            "estimatedFees": snapshot["estimatedFees"],
            "totalFees": str(
                Decimal(snapshot["confirmedFees"])
                + Decimal(snapshot["estimatedFees"])
            ),
        }

    if plan.tool == AnalyticsToolName.COMPARE_PERIODS:
        current = build_calendar_cashflow(user_id, plan.period, anchor=anchor)
        previous = build_calendar_cashflow(
            user_id,
            plan.period,
            anchor=_previous_anchor(plan.period, anchor),
        )
        return {"current": current, "previous": previous}

    if plan.tool == AnalyticsToolName.WHAT_IF:
        trend = build_description_trend(
            user_id,
            plan.query or "",
            plan.period,
            anchor=anchor,
        )
        current = Decimal(trend["totalAmount"])
        reduction = Decimal(plan.reduction_percent or 0) / Decimal("100")
        return {
            "query": trend["query"],
            "period": trend["period"],
            "currentAmount": str(current),
            "reductionPercent": plan.reduction_percent,
            "illustrativeReduction": str((current * reduction).quantize(Decimal("0.01"))),
            "illustrativeRemaining": str((current * (1 - reduction)).quantize(Decimal("0.01"))),
            "warning": "This is an illustration, not a prediction or automatic budget change.",
        }

    summary = build_analytics_summary(user_id, "12-months", today=anchor)
    if plan.tool == AnalyticsToolName.COMMITMENT_PRESSURE:
        return {
            "period": summary["period"],
            "commitments": summary["commitments"],
            "upcoming": summary["upcoming"],
        }
    if plan.tool == AnalyticsToolName.GOAL_PROGRESS:
        return {"period": summary["period"], "goals": summary["goals"]}
    if plan.tool == AnalyticsToolName.DEBT_POSITION:
        return {"period": summary["period"], "debts": summary["debts"]}

    raise ValueError(f"Unsupported analytics tool: {plan.tool}")

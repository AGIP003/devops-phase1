from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class AnalyticsToolName(StrEnum):
    SEARCH_SPENDING = "search_spending"
    COMPARE_PERIODS = "compare_periods"
    FEE_SUMMARY = "get_fee_summary"
    CASHFLOW_SUMMARY = "get_cashflow_summary"
    COMMITMENT_PRESSURE = "get_commitment_pressure"
    GOAL_PROGRESS = "get_goal_progress"
    DEBT_POSITION = "get_debt_position"
    WHAT_IF = "run_what_if_scenario"


class AnalyticsQuestionPlan(BaseModel):
    """Strict read-only operation chosen from a user's finance question."""

    tool: AnalyticsToolName
    period: str = Field(pattern=r"^(week|month|year)$")
    query: str | None = Field(default=None, max_length=100)
    reduction_percent: int | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def validate_tool_arguments(self):
        if self.tool in {
            AnalyticsToolName.SEARCH_SPENDING,
            AnalyticsToolName.WHAT_IF,
        }:
            if not self.query or len(self.query.strip()) < 2:
                raise ValueError("This analytics operation requires a search query")
        if self.tool == AnalyticsToolName.WHAT_IF:
            if self.reduction_percent is None:
                raise ValueError("A what-if operation requires a reduction percentage")
        elif self.reduction_percent is not None:
            raise ValueError("Only a what-if operation accepts a reduction percentage")
        return self


class AnalyticsAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=1200)
    evidence: list[str] = Field(default_factory=list, max_length=6)
    caveats: list[str] = Field(default_factory=list, max_length=4)


class WeeklyFinanceNarrative(BaseModel):
    headline: str = Field(min_length=1, max_length=140)
    summary: str = Field(min_length=1, max_length=900)
    # A quiet or newly created account may have nothing defensible to call an
    # observation. An empty list is more truthful than forcing the model to
    # invent one merely to satisfy the response schema.
    observations: list[str] = Field(default_factory=list, max_length=5)
    options: list[str] = Field(default_factory=list, max_length=4)
    caveats: list[str] = Field(default_factory=list, max_length=4)

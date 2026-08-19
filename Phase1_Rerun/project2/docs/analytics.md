# Personal analytics

## API

```http
GET /api/analytics/summary?period=12-months
Authorization: Bearer <access-token>
```

Supported periods are `30-days`, `90-days`, `6-months`, `12-months` and `all`.
Date boundaries are inclusive. The server derives ownership from the validated
access token and never accepts a `user_id` query parameter.

Responses use `Cache-Control: private, no-store` because they contain a compact
summary of sensitive financial information.

## Metric definitions

| Metric | Definition |
| --- | --- |
| Income | Sum of non-deleted transactions whose category type is `income` inside the period. |
| Expenses | Sum of non-deleted transactions whose category type is `expense` inside the period. |
| Net cash flow | Income minus expenses. |
| Savings rate | Net cash flow divided by income. It is `null` when income is zero. |
| Monthly bills/subscriptions | Active KES commitment amounts normalized to a monthly equivalent. |
| Monthly debt payments | Active KES debt schedules normalized to a monthly equivalent. One-time schedules are excluded. |
| Required goal contribution | Remaining KES goal balance divided by estimated months until its target date. |
| Recorded debt fees | Debt ledger entries whose type is `fee` inside the selected period. These increase debt balance and are not automatically cash expenses. |
| Transaction fees | Unavailable until transactions explicitly represent them. The API returns `null` and the coverage flag is `false`. |

Weekly values use `52 / 12`; quarterly values use `1 / 3`; termly values assume
three occurrences per year; yearly values use `1 / 12`; custom intervals use
`365.2425 / interval_days / 12`. These are monthly estimates, not invoices.

## Response sections

- `cashFlow`: actual transaction movement.
- `commitments`: estimated recurring and planned monthly pressure.
- `budget`: current budget targets and recorded actual amounts.
- `debts`: current active balance, period repayments, fees and schedules.
- `goals`: target, saved balance, progress and required monthly contribution.
- `monthlyTrend`, `expenseCategories`, `dailyActivity`: chart-ready aggregates.
- `upcoming`: the next eight KES commitments or debt payments.
- `adjustmentOpportunities`: deterministic review flags with visible evidence.
- `coverage`: which source domains are implemented.
- `warnings`: material exclusions such as unsupported currencies.

## Adjustment rules

The first implementation uses deterministic rules rather than AI. It flags a
category when it represents at least 30% of period expenses, reports recorded
debt fees, and flags estimated monthly commitments at or above 60% of average
monthly income. The language asks users to review evidence; it does not instruct
them to cancel a service or make a financial decision.

## Calendar

The ECharts calendar shows one selected month on every screen size. Every date
cell displays its day number and the larger of that day's income or expense
totals in the user's selected display currency. Income-dominant cells use green
and a `+` prefix; expense-dominant cells use red and a `−` prefix; equal or empty
days are neutral. The prefixes ensure meaning does not depend on colour alone.
Tooltips show the full income, expense and transaction count for the date.

## Chart-led frontend and What-if Lab

The Analytics route presents six visual questions: cash-flow movement, category
spending, monthly commitments, budget/goal progress, debt position and daily
expense rhythm. Its insight rail refreshes from the summary endpoint whenever
the period changes or the user explicitly requests fresh data.

The What-if Lab lets a user select one expense category and explore possible
category and subscription reductions. Category totals are normalized to a
monthly average over the selected period. Scenarios exist only in React state:
they are not stored, do not change budgets or transactions, and are labelled as
illustrations rather than recommendations or guaranteed savings.

## Operational checks

Focused backend test:

```bash
./venv/bin/python -m pytest -q tests/test_analytics_orm.py
```

Frontend checks:

```bash
cd tracker-frontend
npm test -- --run src/pages/Analytics.test.jsx
npm run lint
npm run build
```

Before introducing caching, record endpoint latency and query plans with a
controlled larger dataset. Cache only authenticated, user-specific results and
invalidate or expire them when the underlying finance records change.

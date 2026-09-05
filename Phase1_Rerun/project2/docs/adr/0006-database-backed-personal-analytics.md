# ADR 0006: Database-backed personal analytics read model

## Status

Accepted on 18 August 2026.

## Context

The Analytics page must combine actual transactions with budgets, savings goals,
debts, bills, subscriptions and recorded debt fees. Downloading every underlying
row into the browser would increase response size, expose more financial detail
than the page needs, and make every client reproduce the same definitions.

These domains also have different meanings. A transaction is actual cash
movement, while a bill or subscription is a future commitment. Adding them
together as expenses would double-count a commitment after it is paid and
recorded as a transaction.

## Options considered

1. Fetch every record and calculate in React. Simple initially, but it scales
   poorly and duplicates financial rules across clients.
2. Build one large SQL join. It uses the database, but one-to-many relationships
   multiply rows and can silently inflate totals.
3. Run purpose-specific aggregate queries behind one summary endpoint. This
   keeps definitions server-side and avoids row multiplication.
4. Maintain precomputed analytics tables. Fast reads, but adds jobs, freshness
   rules and recovery complexity that current usage does not justify.

## Decision

Use `GET /api/analytics/summary?period=<period>` as an authenticated read model.
The service runs small, user-scoped aggregate queries for each financial domain
and combines their summaries. React receives only the data required to render
the page.

Actual cash flow remains separate from estimated monthly commitments. Debt fees
remain separate from transaction fees. Transaction fees are reported as
unavailable until the transaction schema explicitly represents them.

Apache ECharts is isolated behind a React wrapper and loaded only with the lazy
Analytics route. This allows the visualization library to be replaced without
changing the API or financial calculations.

## Consequences

- Metric definitions and authorization live in one backend boundary.
- Network response size grows with summary buckets, not raw transaction count.
- Several small queries are executed per request. This is safer than a
  row-multiplying join but must be monitored as traffic grows.
- Free-text descriptions and merchant names remain separate dimensions:
  category answers “where,” description answers “what for,” and merchant
  answers “who.” Only normalized aggregates are returned; raw rows stay behind
  the authenticated transaction endpoint.
- Calendar offsets represent “last week/month/year” explicitly. They are not
  treated as rolling windows, and all-time queries carry recorded-history
  coverage so an empty result is not overstated.
- Monthly equivalents use documented annualization assumptions.
- Currency values other than KES are excluded from combined commitment and goal
  totals until conversion-at-measurement is designed.
- The ECharts Analytics chunk is approximately 211 KB compressed in the first
  production build; lazy loading protects the initial application route.

## Revisit when

- Analytics latency approaches the application's slow-request threshold.
- Aggregate-query count or PostgreSQL load becomes material; at that point,
  measure before adding short-lived caching or precomputed read models.
- Query volume materially affects PostgreSQL CPU or connection capacity.
- Users commonly have enough history that monthly or daily result buckets need
  pagination or pre-aggregation.
- Multi-currency historical conversion is implemented.
- Transaction fees receive an explicit data model.

Likely next steps at larger scale are short-lived per-user/period caching,
followed by asynchronously refreshed aggregate tables only if measurements
justify them.

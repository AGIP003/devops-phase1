# ADR 0004: Model bills and subscriptions as recurring commitments

- Status: Accepted
- Date: 2026-08-17

## Context

MoneyTiq needs to distinguish recurring obligations from ordinary transactions.
A hotel lunch is a completed transaction, an unpaid hospital balance is a debt,
and electricity or Spotify is a recurring commitment. Treating all purchases as
bills would create noisy reminders and misleading forecasts.

The feature must preserve payment history, enforce user ownership, accept future
trusted Telegram/import commands, handle variable bills, and work without Redis
or a background scheduler in v1.

## Options considered

1. Separate `bills` and `subscriptions` tables. This makes each table simple but
   duplicates ownership, recurrence, history, status and ingestion logic.
2. One `recurring_commitments` table with a `kind` discriminator and a separate
   occurrence ledger. This shares true invariants while retaining bill- and
   subscription-specific validation.
3. Store recurrence as JSON inside the user row. This reduces tables but weakens
   constraints, indexing, querying, referential integrity and history handling.
4. Pre-generate every future occurrence with a scheduled worker. This enables
   richer reminders, but adds scheduling, retry and duplicate-delivery problems
   before the app needs them.

## Decision

Use one normalized `recurring_commitments` table and one append-only
`commitment_occurrences` table.

- `kind` is `bill` or `subscription`; both are recurring by definition.
- Bills may have a fixed or estimated amount. Subscriptions use a fixed amount.
- A successful paid/skipped command appends one occurrence and advances the next
  due date inside the same database transaction.
- Each command advances exactly one cycle. An item several months overdue stays
  overdue until each missing cycle is deliberately resolved.
- Calendar cycles retain their original day. A January 31 monthly item becomes
  February 28 and then March 31 instead of drifting permanently to the 28th.
- `termly` is explicitly defined as every four calendar months in v1.
- Cancellation stops new cycles but keeps the visible record. Soft archive hides
  it from normal views while preserving history.
- Source/reference unique constraints prepare for idempotent Telegram and import
  commands without implementing parsers now.
- No transaction is automatically created when a cycle is paid in v1.

## Reasons

The chosen design removes duplicated recurrence code, maintains an auditable
ledger, supports variable bill amounts, and needs no queue or scheduler. Database
checks protect invariants even when future ingestion does not use the React form.
Row locking serializes simultaneous cycle updates so two requests cannot advance
the same due date from one starting state.

## Consequences

- Monthly summary figures are estimates normalized from each cadence; they are
  planning guidance, not accounting totals.
- A user must confirm paid or skipped cycles; v1 does not detect provider charges.
- `termly` may not match a particular school's dates and must be explained in UI.
- Archived rows remain personal financial data and need a future retention rule.
- Permanent deletion and restore views are intentionally deferred until a shared
  lifecycle design covers debts, goals and commitments consistently.

## Revisit when

- users need pre-due reminders or automatic overdue notifications;
- payment imports can safely reconcile occurrences with transactions;
- term dates must be institution-specific rather than four-month intervals;
- shared household commitments require multi-user ownership;
- monitoring shows that due-date queries require a partial active-row index.

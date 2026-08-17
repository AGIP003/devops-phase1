# ADR 0005: Correct activity rows instead of overwriting calculated totals

- Status: Accepted
- Date: 2026-08-17

## Context

Users can mistype a repayment, saving contribution or recurring payment. The UI
needs a simple correction path, but balances and progress totals are calculated
from activity. Directly editing a displayed total would make it disagree with
the rows that supposedly produced it.

## Options considered

1. Let users overwrite the displayed total. This is simple but creates
   contradictory financial history.
2. Never edit activity; append reversal and replacement rows. This gives a strong
   audit trail but adds accounting concepts and UI complexity beyond v1 needs.
3. Edit the specific owned activity row and recalculate every derived total.
   Existing timestamps record that a change occurred, although earlier values
   are not retained.

## Decision

Choose option 3 for v1.

- Plan details and activity are edited separately.
- Balances, progress and repayment totals remain derived values.
- Every lookup includes the authenticated owner's user ID; another user's ID is
  indistinguishable from a missing resource.
- A debt repayment linked to a transaction updates both rows in one database
  transaction, so either both succeed or neither does.
- Editing an already-recorded commitment occurrence does not advance its due date
  again.
- Corrections that produce an impossible negative saving or debt balance fail.

## Consequences

Users can fix ordinary input mistakes without learning reversal accounting. The
database stays internally consistent and the existing model timestamps are
enough for current product support. This is not an immutable compliance audit
log: if regulatory or shared-account requirements later demand prior-value
history, introduce versioned changes or reversal entries through a new reviewed
migration and UX.

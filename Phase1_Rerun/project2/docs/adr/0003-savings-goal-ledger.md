# ADR 0003: Savings goal ledger

## Status

Accepted on 2026-08-16.

## Context

MoneyTiq needs simple savings goals without treating savings as expenses or
requiring users to classify account transfers. Future Telegram commands must
use the same business rules as the web interface and must not create duplicate
entries when a message is retried.

## Decision

A goal stores the plan: name, target, target date, and weekly, fortnightly, or
monthly contribution frequency. A separate activity table stores each
contribution or withdrawal. The current balance and suggested contribution are
derived rather than maintained as independently editable totals.

Activity may be corrected when the user made an input mistake, following ADR
0005, but it cannot be dated in the future. Suggestions use the confirmed
balance and the periods from the current date to the target date.

The browser uses `created_via=manual`. Trusted future adapters may call the
service with `created_via=telegram` and an `external_reference` such as a
Telegram update ID. A database unique constraint makes retries idempotent.

Transactions are deliberately not linked in v1. Moving money into savings is
usually a transfer, not an expense, and the current transaction model does not
yet represent accounts and transfers accurately.

## Consequences

- The UI can remain compact while retaining an auditable activity history.
- Withdrawals do not require rewriting a stored balance.
- Suggested contributions change as time and the balance change.
- Telegram integration can be added without creating a second goal system.
- Account transfers require a later, explicit design decision.

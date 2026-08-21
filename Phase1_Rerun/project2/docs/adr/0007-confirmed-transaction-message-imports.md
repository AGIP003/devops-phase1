# ADR 0007: Confirmed and idempotent transaction-message imports

- Status: Accepted
- Date: 2026-08-20

## Context

Telegram users want to paste M-Pesa and Airtel Money messages instead of typing
amounts and dates manually. Provider messages contain useful facts, but they also
contain private balances and identifiers, may be delivered more than once, and
cannot explain what a purchase meant to the user. Saving immediately after a
regex match would create silent classification errors and duplicate spending.

## Options considered

1. Parse and save directly in the Telegram process. This is quick, but duplicates
   business rules and cannot enforce database-backed idempotency.
2. Parse in Telegram and call the ordinary transaction endpoint. This reuses
   transaction creation but loses provider provenance, fees and duplicate guards.
3. Preview through a central backend parser, require user description/category
   confirmation, then atomically create the transaction and a minimal import row.

## Decision

Choose option 3.

- A complete provider-looking SMS can start the preview automatically; `/import`
  remains an explicit alternative. A conservative local prefix gate prevents
  ordinary chat from being sent for financial parsing, and unsupported text
  returns to normal welcome handling.
- No parsed message becomes a financial instruction until the user supplies a
  description, chooses a category and confirms the final preview.
- Regex performs deterministic fact extraction. Full-pattern matching prevents
  partial messages from being accepted as complete transactions.
- A user-written description and selected category are mandatory. The parser's
  merchant text is context, not the user's intent.
- Data bundles and airtime are suggested as the `airtime` category.
- User aliases and deterministic rules run before any future AI categorizer.
  The user must explicitly choose **Save & remember** before an alias is stored.
- Future AI receives only a minimized description, generalized merchant label,
  direction and candidate categories—not raw SMS, balances, references, phone
  numbers or account numbers. Its answer remains a suggestion.
- `transaction_imports` stores provider, reference, fingerprint, original time,
  subtype, currency and fee. Raw messages and resulting wallet balances are not
  persisted.
- Unique constraints on owner/provider/reference and owner/fingerprint make a
  repeated request safe. Transaction, provenance and optional alias commit as
  one ACID unit.
- Fuliza notices are recognized but do not create a debt or duplicate expense.
  Withdrawals remain transfers and wait for an account-transfer model.
- Failed provider notices are silently ignored during automatic detection and
  never reach transaction creation.
- When a successful provider message omits its transaction date, the user must
  supply the date. The system does not substitute the Telegram receipt time or
  today's date; unknown provider timestamps remain `NULL` in import provenance.

## Consequences

There is one extra row per imported transaction and an additional database write,
which is negligible at current scale. In exchange, analytics can distinguish
provider fees and retries cannot inflate spending. The same backend boundary can
later serve statement imports without moving financial rules into Telegram.

The fingerprint uses a purpose-derived HMAC key and never exposes the source SMS.
Provider reference uniqueness remains the stable guard if the application secret
is rotated. Message formats can still change; unsupported messages fail closed
and require a reviewed parser fixture before support is expanded.

## Revisit when

- Account-to-account transfers and cash-wallet balances are modelled.
- Fuliza lifecycle tracking is explicitly designed.
- An AI categorizer has a documented provider, privacy assessment and evaluation
  set.
- Provider APIs replace user-supplied messages as an authoritative source.

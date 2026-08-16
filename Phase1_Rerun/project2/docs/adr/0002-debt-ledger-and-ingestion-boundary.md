# ADR 0002: Debt ledger and ingestion boundary

## Context

MoneyTiq needs to track debts created manually today and later proposed by
Telegram, SMS, or statement parsers. A debt may be partially repaid before it is
first entered, may have optional interest or fees, and may have several later
repayments. Updating only `balance` and `paid_amount` would discard that history
and make duplicate parser deliveries hard to detect.

## Options considered

1. Store only the latest balance on one debt row. This is simple, but loses the
   reason the balance changed and is fragile under imports and retries.
2. Store a debt plus repayment rows. This preserves repayments but needs another
   redesign when interest, fees, and adjustments are introduced.
3. Store a debt plus typed ledger entries, an optional schedule, and declared fee
   terms. This adds tables but keeps each concept explicit and testable.

## Decision

Use option 3.

- `debts` stores the obligation and its balance when MoneyTiq starts tracking it.
- `debt_entries` stores repayments, reported interest, actual fees, and reviewed
  adjustments after tracking begins.
- `debt_schedules` stores zero or one active repayment plan.
- `debt_fee_terms` stores controlled fee categories and an explicit `other`
  label without turning spelling variants into new global categories.
- The service accepts a trusted `created_via` and optional external reference.
  Browser routes always set `created_via=manual`; future adapters will supply
  parser references. Unique constraints make retries idempotent.
- MoneyTiq records lender/user-reported interest. It does not calculate interest
  from a rate because flat, reducing-balance, and compounding rules differ.
- Fuliza is not a preset in the first release because an overdraft/credit line
  has different lifecycle semantics from a fixed debt.

## Consequences

- Current balance is opening balance plus increasing entries minus repayments
  and decreasing adjustments.
- Existing debts can start from a known current balance without reconstructing
  their entire history.
- Adding an entry and an optional linked transaction must share one database
  transaction so partial records cannot survive a failure.
- Balance queries load entry rows. This is appropriate at current scale; a
  measured aggregate query or cached balance can be introduced later.
- Notes, counterparty labels, and debt descriptions are personal financial data.
  Request logs must not include payload bodies.

## Revisit when

- MoneyTiq implements revolving overdrafts or credit limits.
- Entry volume makes loading entry rows measurably slow.
- A licensed integration provides authoritative amortisation schedules.
- Multiple concurrent repayment schedules per debt become a real requirement.

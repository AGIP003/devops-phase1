# ADR 0008: Separate provider flow from transaction classification

- Status: Accepted
- Date: 2026-09-06

## Context

A provider message can prove that money entered or left one wallet, but it
cannot always prove what that movement means to the user. Moving KES 17,500
from a user's Airtel Money wallet to their M-Pesa wallet produces one outgoing
message and one incoming message. Calling those records an expense and income
inflates both totals even though the user's money merely changed location.

Names are not ownership evidence. A SIM or account may be registered under a
relative's name, and the same person may also make a genuine payment. A single
reported closing balance is also insufficient to calculate a balance change
without a trustworthy preceding balance.

## Decision

- Provider flow is evidence with two values: `money_in` and `money_out`.
- Reporting classification is a separate user-facing choice: `income`,
  `expense`, or `transfer`.
- Known purchases, airtime and loan repayments keep their deterministic expense
  suggestion. Person-to-person sends, receipts, PayBill messages and all AI
  fallbacks require explicit classification before saving.
- The backend permits `money_in` to become income or transfer, and `money_out`
  to become expense or transfer. Contradictory combinations are rejected.
- Transfers use the `Internal Transfer` category and are excluded from income,
  expense, net-cash-flow and savings-rate totals.
- An explicit provider fee remains an expense even when its principal is an
  internal transfer.
- Regex reads the stable financial core and ignores promotional suffixes. AI
  cannot override an issuer inferred from the provider's reviewed reference
  format or reverse explicit received/sent/paid wording.
- Category identity includes owner, name and type. This permits a label such as
  `Loan` to exist independently for income and expense and fixes type changes
  that previously reused a category carrying the old type.

## Fuliza boundary

Fuliza principal remains financing rather than ordinary income or consumer
spending. A draw increases available cash and liability; a repayment reduces
cash and liability. The original financed purchase is the expense. Explicit
access and maintenance fees are added to expense analytics separately. This
prevents counting the financed purchase and principal repayment twice.

## Consequences

Ambiguous imports require one extra tap, trading a small amount of friction for
trustworthy analytics. Existing incorrectly classified production records are
not rewritten automatically because raw messages were deliberately not stored
and ownership cannot be reconstructed safely. Users can reclassify reviewed
records through the transaction editor after deployment.

An account ledger could later link both sides of a transfer. Until then, the
single transfer classification keeps movements visible while excluding them
from income and spending totals.

# Debt tracking

## Purpose

The debt feature tracks obligations the authenticated user owes or is owed. It
supports manual entry now and exposes a source-neutral service boundary for later
Telegram, SMS, and statement-parser proposals. Parsing is deliberately not part
of this release.

## Data model

- `debts` stores the description, direction, category, starting balance, optional
  reported interest terms, source, and lifecycle state.
- `debt_schedules` stores zero or one active repayment plan.
- `debt_fee_terms` stores the kinds of fees the user says apply.
- `debt_entries` stores actual repayments, reported interest, charged fees, and
  reviewed balance adjustments after tracking begins.

For a new debt, opening balance is:

```text
original amount - amount already repaid
```

For an existing debt, the user-reported current outstanding balance becomes the
opening balance. Historical charges must not be added again.

After tracking starts:

```text
current balance
= opening balance
+ reported interest entries
+ fee entries
+ increase adjustments
- repayments
- decrease adjustments
```

MoneyTiq does not calculate interest from a stated rate. Loan calculation methods
vary, so only actual amounts reported by the user or lender change the balance.

## API

All endpoints require a bearer token. Identity comes from that token; no endpoint
accepts a client-provided `user_id`.

### List debts

```http
GET /api/debts
```

### Create a debt

```http
POST /api/debts
Content-Type: application/json

{
  "title": "Amina lunch advance",
  "direction": "owed_to_me",
  "category": "personal",
  "trackingKind": "existing",
  "currentBalance": "8500.00",
  "amountAlreadyRepaid": "0",
  "currencyCode": "KES",
  "hasInterest": false,
  "feeTerms": [],
  "schedule": {
    "frequency": "one_time",
    "intervalCount": 1,
    "installmentAmount": "8500.00",
    "nextDueDate": "2026-08-30",
    "finalDueDate": "2026-08-30"
  }
}
```

### Get one owned debt

```http
GET /api/debts/{debt_id}
```

An unknown debt and another user's debt both return `404` to avoid disclosing
whether the identifier exists.

### Edit debt details

```http
PATCH /api/debts/{debt_id}
```

This accepts the same debt fields as creation and updates the plan without
discarding repayment history. The server recalculates the outstanding balance
from the corrected opening amount and the existing activity rows. It rejects an
opening amount that would make that calculated balance negative.

### Record debt activity

```http
POST /api/debts/{debt_id}/entries
Content-Type: application/json

{
  "entryType": "repayment",
  "amount": "1000.00",
  "occurredOn": "2026-08-16",
  "createTransaction": true,
  "paymentMethod": "m-pesa"
}
```

When `createTransaction` is true, the repayment entry and normal MoneyTiq
transaction share one database commit. A failure rolls both back.

### Correct debt activity

```http
PATCH /api/debts/{debt_id}/entries/{entry_id}
Content-Type: application/json

{
  "entryType": "repayment",
  "amount": "900.00",
  "occurredOn": "2026-08-16",
  "notes": "Corrected amount"
}
```

The outstanding balance is derived again after the correction. If a repayment
created a transaction, MoneyTiq updates that transaction's amount, date and
description in the same database transaction. A linked repayment cannot be
changed into interest or a fee because its transaction would then describe a
different financial event.

### Archive a debt

```http
DELETE /api/debts/{debt_id}
```

Archiving is a soft deletion: normal API queries hide the debt while PostgreSQL
retains its history for a later reviewed retention/deletion workflow.

## Future ingestion

Trusted adapters will create `CreateDebtInput` or `CreateDebtEntryInput` commands
with `created_via` and `external_reference`. Unique constraints make repeat
deliveries idempotent. Browser payloads cannot set those trusted fields.

Parser output must initially be a proposal that the user confirms. Raw SMS or
statement contents should not be copied into debt notes or application logs.

## Test guarantees

- Opening and current balances are calculated correctly.
- Repayments, interest, fees, and adjustments have the correct sign.
- Other users receive `404` and cannot mutate the debt.
- Owners can correct details and activity without replacing calculated totals.
- Custom fees require a name.
- A linked repayment and its transaction stay consistent after correction.
- Linked transaction failures roll back the entire operation.
- Repeated external references do not create duplicate debts.
- Archived debts are hidden but preserved.

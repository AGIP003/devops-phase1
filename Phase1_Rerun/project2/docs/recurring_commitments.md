# Bills and subscriptions

## Domain boundary

- Transaction: money that already moved, such as lunch.
- Debt: an outstanding balance, such as an unpaid hospital account.
- Bill: a recurring obligation whose amount may be fixed or estimated.
- Subscription: a recurring service or membership with a fixed expected amount.

The frontend never asks whether an item is one-time. One-time spending belongs in
transactions or debts rather than this feature.

## API

All endpoints require a bearer access token. The server derives the internal user
ID from that token and includes it in every lookup; callers cannot supply a user
ID.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/commitments` | List the current user's non-archived items |
| `GET` | `/api/commitments/{id}` | Fetch one owned item |
| `POST` | `/api/commitments` | Create a bill or subscription |
| `POST` | `/api/commitments/{id}/cycles` | Record a paid or skipped cycle |
| `PATCH` | `/api/commitments/{id}/status` | Cancel or reactivate recurrence |
| `DELETE` | `/api/commitments/{id}` | Soft-archive an item |

Example bill:

```json
{
  "kind": "bill",
  "name": "Electricity",
  "provider": "Kenya Power",
  "category": "Utilities",
  "amount": "2500.00",
  "amountKind": "estimated",
  "nextDueDate": "2026-08-31",
  "frequency": "monthly",
  "currencyCode": "KES"
}
```

Example payment:

```json
{
  "resolution": "paid",
  "actualAmount": "2318.40",
  "resolvedOn": "2026-08-29",
  "notes": "Paid by M-Pesa"
}
```

## Integrity and failure behavior

- PostgreSQL checks kind, cadence, amounts, lifecycle status, custom interval and
  subscription auto-renew consistency.
- Ownership-safe queries return `404` for another user's guessed ID. This avoids
  confirming whether that resource exists.
- Cycle resolution locks the commitment row, writes history and advances the due
  date in one ACID transaction. A failure rolls back both changes.
- Future external commands use `(owner, source, external_reference)` uniqueness.
  Retrying the same Telegram message returns the existing result rather than
  adding another cycle.
- Responses use `Cache-Control: private, no-store` because payment schedules are
  private financial information.

## Operations

Apply the migration locally or in the deployment pre-start phase:

```bash
flask db upgrade head
flask db current
```

Expected head: `c8f1a4e72b09`.

Linux+ note: the Flask process opens a PostgreSQL Unix-domain socket locally.
`ss -lx | rg PGSQL` shows listening local sockets; `psql -d finance_tracker_local
-c '\conninfo'` proves the target database and role. Never print a full database
URL because it can contain a password.

Run focused evidence:

```bash
python -m pytest -q tests/test_recurring_commitment_orm.py
cd tracker-frontend
npm test -- --run src/pages/Bills.test.jsx
```

Before production deployment, back up PostgreSQL, verify the environment points
at the intended service, apply the migration once, and smoke-test creating and
archiving a temporary item owned by a dedicated test account.

## Privacy and retention

Names, providers, notes, amounts and due dates reveal financial behavior. Do not
place them in request logs or send them to external AI providers by default.
Archive is not erasure: archived rows and their occurrences remain in PostgreSQL.
The project-wide retention and account-deletion workflow must explicitly cover
both tables before permanent deletion is exposed in the UI.

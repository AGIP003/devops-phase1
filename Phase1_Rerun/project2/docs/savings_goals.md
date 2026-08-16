# Savings goals

Savings goals deliberately do not create or link expense transactions. A goal
stores a plan, while its entries record confirmed additions and withdrawals.

## Suggested contribution

The service calculates:

```text
remaining amount = max(target amount - current savings, 0)
suggested contribution = remaining amount / remaining periods
```

Weekly periods use seven-day intervals, fortnightly periods use fourteen-day
intervals, and monthly periods use calendar months. The result rounds upward to
the nearest cent so repeated rounding cannot leave the goal slightly short.

## API

All routes require authentication and derive ownership from the access token.
They never accept a client-provided user ID.

### `GET /api/goals`

Lists the authenticated user's non-archived goals.

### `POST /api/goals`

```json
{
  "name": "Emergency fund",
  "targetAmount": "120000.00",
  "currentSavings": "20000.00",
  "targetDate": "2026-12-31",
  "contributionFrequency": "monthly",
  "currencyCode": "KES",
  "notes": "Three months of essential expenses"
}
```

`currentSavings` is optional. When supplied, it creates an opening contribution
entry rather than a mutable balance shortcut.

### `GET /api/goals/{goal_id}`

Returns one owned, non-archived goal. An unknown or another user's ID returns
404 to avoid disclosing whether the record exists.

### `POST /api/goals/{goal_id}/entries`

```json
{
  "entryType": "contribution",
  "amount": "5000.00",
  "occurredOn": "2026-08-16",
  "notes": "Weekly saving"
}
```

`entryType` is `contribution` or `withdrawal`. A withdrawal cannot exceed the
current saved balance.

### `DELETE /api/goals/{goal_id}`

Soft-archives the goal and preserves its activity for recovery and audit.

## Future ingestion boundary

Trusted Telegram or import adapters call the service layer directly with a
supported `created_via` value and an `external_reference`. The uniqueness
constraints make retried messages safe. Public browser payloads cannot choose
their own source or external reference.

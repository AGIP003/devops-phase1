# Week 8 API Compatibility Report

## Decision

The Week 8 data-layer refactor is **backward-compatible with the existing web
frontend and Telegram bot for the exercised workflows**. Routes, HTTP methods,
authentication headers, primary request fields, and serialized response fields
were retained while raw `psycopg2` queries were replaced by SQLAlchemy ORM
services.

No compatibility claim is made for undocumented clients or endpoints that were
not exercised. This report records observed and tested behaviour; it is not a
substitute for a versioned OpenAPI contract suite.

## What changed behind the API

```text
Before: route -> raw SQL helper -> psycopg2 cursor -> PostgreSQL row/dict

After:  route -> domain service -> SQLAlchemy session/model -> PostgreSQL
          |
          +-> explicit serializer -> existing JSON shape
```

The serializer boundary is the main compatibility protection. ORM models are
Python objects with relationships and `Decimal`, `date`, and `datetime` values;
the API still emits the field names and JSON-friendly values expected by the
frontend.

## Authentication contract

Authenticated routes still require:

```http
Authorization: Bearer <JWT>
```

Registration and login continue to return a token and a public user object.
`password_hash` is never serialized. A missing or invalid token produces HTTP
401.

Ownership is enforced inside every user-scoped service query, not by trusting
an ID supplied by the browser. A logged-in user who guesses another user's
transaction, budget, or item ID receives HTTP 404. Returning 404 avoids
confirming whether the resource exists for another owner.

## Transaction API

### Endpoint matrix

| Method | Path | Compatibility | Notes |
| --- | --- | --- | --- |
| `GET` | `/api/transactions` | Retained | Optional `query` searches descriptions case-insensitively |
| `POST` | `/api/transactions` | Retained | Creates a transaction for the authenticated user |
| `GET` | `/api/transactions/<id>` | Retained | Owner-only; excludes soft-deleted rows |
| `PUT` | `/api/transactions/<id>` | Retained | Partial update; owner-only |
| `DELETE` | `/api/transactions/<id>` | Retained behaviour, safer persistence | Now records `deleted_at` instead of physically deleting the row |
| `GET` | `/admin/transactions` | Retained | Admin-only; excludes soft-deleted rows |

### Create request

The required request shape remains:

```json
{
  "amount": "300.00",
  "category": "food",
  "type": "expense",
  "date": "2026-08-14",
  "description": "private lunch",
  "payment_method": "m-pesa"
}
```

Required fields are `amount`, `category`, `type`, `date`, and
`payment_method`. `description` is optional. The route validates HTTP input and
converts it to domain types before calling the service:

- amount -> Python `Decimal`;
- date -> Python `date`;
- category/type -> normalized validated strings;
- payment method -> case-insensitive database lookup.

Payment-method case is ignored, but punctuation is not invented:
`M-PESA` matches `m-pesa`; `mpesa` does not automatically match `m-pesa`.

### Transaction response

The serializer returns:

```json
{
  "id": 42,
  "user_id": 2,
  "date": "2026-08-14",
  "description": "private lunch",
  "type": "expense",
  "category": "food",
  "amount": "300.00",
  "payment_method": "m-pesa"
}
```

Compatibility details:

- `amount` remains a string, avoiding binary floating-point corruption in
  financial values;
- `date` remains an ISO 8601 date string;
- category and payment-method names are loaded from relationships but exposed
  as plain strings;
- internal foreign keys such as `category_id` and `payment_method_id` are not
  added to the public response;
- absent optional relationships serialize as `null` instead of causing an
  attribute error.

`POST` and `PUT` wrap this object in `data`; list and detail `GET` responses
retain their existing unwrapped shapes.

### Intentional soft-delete behaviour

`DELETE /api/transactions/<id>` still returns success to the frontend, but the
database row is preserved with a non-null `deleted_at`. Normal user and admin
queries filter on `deleted_at IS NULL`, so deleted transactions disappear from
the API. This is an internal persistence change, not a request/response break.

## Budget API

| Method | Path | Compatibility | Notes |
| --- | --- | --- | --- |
| `GET` | `/api/budgets` | Retained | Owner-only; returns `Cache-Control: private, no-store` |
| `POST` | `/api/budgets` | Retained | Requires at least one item |
| `PUT` | `/api/budgets/<id>` | Retained | Replaces the submitted budget item collection |
| `DELETE` | `/api/budgets/<id>` | Retained | Owner-only hard delete with item cascade |
| `PATCH` | `/api/budget-items/<id>` | Retained | Accepts a boolean `checked` field only |

The public budget shape remains camel-cased for the frontend:

```json
{
  "id": 2,
  "userId": 2,
  "name": "Updated ORM Budget",
  "category": "Backend Learning",
  "targetAmount": 1200.0,
  "lastSpend": 0.0,
  "lastUsedAt": "2026-08-08T15:15:24.526782+00:00",
  "items": [
    {
      "id": 5,
      "name": "Advanced SQLAlchemy book",
      "estimatedAmount": 700.0,
      "actualAmount": 0.0,
      "checked": false,
      "position": 0
    }
  ]
}
```

`Budget.items` is now an ORM relationship, but the serializer sorts it by
`position` and then `id`, preserving stable frontend ordering. Ownership of an
item is established through its parent budget; possessing an item ID alone is
not authorization.

## Telegram API

The current Telegram design was migrated to ORM services without introducing a
duplicate schema or alternate data store.

| Method | Path | Compatibility | Important behaviour |
| --- | --- | --- | --- |
| `POST` | `/api/telegram/link-token` | Retained | Authenticated; 10-minute, single-use token |
| `POST` | `/api/telegram/verify` | Retained | Links a positive integer Telegram ID |
| `GET` | `/api/telegram/status` | Retained | Returns `linked` and `telegram_id` |
| `DELETE` | `/api/telegram/unlink` | Retained | Clears the link |
| `POST` | `/api/telegram/session` | Retained | Bot-authenticated session exchange |
| `GET` | `/api/telegram/preferences` | Retained | Returns payment method and alias map |
| `PUT` | `/api/telegram/preferences` | Retained | Persists aliases through PostgreSQL JSONB |

Security behaviours now have automated evidence:

- a link token cannot be reused;
- an expired token is rejected;
- one Telegram account cannot silently replace another user's link;
- preferences survive a database round trip;
- bot session exchange uses a constant-time comparison of the hashed bot
  credential.

## Error compatibility

Application error responses retain the common structure:

```json
{
  "error": "Not found",
  "message": "Transaction not found"
}
```

Relevant status codes are:

| Status | Meaning in this API |
| --- | --- |
| 400 | Invalid JSON, missing/invalid field, expired or reused link token |
| 401 | Missing or invalid authentication |
| 403 | Authenticated but forbidden administrative operation |
| 404 | Resource absent, soft-deleted, or not owned by this user |
| 409 | Unique-resource conflict, such as an email or Telegram ID already in use |
| 500 | Unexpected server failure; internal details are not returned |
| 503 | Telegram schema or bot configuration is temporarily unavailable |

## Compatibility evidence

Automated tests proved:

- transaction owner can create and read a transaction;
- a second authenticated user cannot read, update, or delete it;
- soft delete hides the row from the API while preserving it in PostgreSQL;
- a failed multi-record transaction rolls back and the session recovers;
- a second user cannot access another user's budget or budget item;
- Telegram tokens are single-use and expire;
- Telegram preferences persist through JSONB;
- existing Telegram transaction-parser tests remain green.

The complete suite passed with 15 tests after a from-scratch Alembic rebuild.
Production smoke tests then exercised login, transaction CRUD and persistence,
budget CRUD and item toggling, Telegram status/preferences, and Telegram
transaction entry.

## Known compatibility boundaries

- There is not yet a complete contract test covering every response field and
  every error branch.
- The Flask-RESTX documentation resources are not the authoritative contract;
  the real Flask routes and serializers are.
- Transaction search currently covers `description`, not category or payment
  method.
- Budget money values remain JSON numbers for existing frontend compatibility,
  while transaction amounts remain strings. A future API version should make
  financial serialization consistent deliberately, not silently.
- The NSE feature remains a frontend mock; this refactor does not claim an NSE
  backend API.

Future endpoint changes should update this document and add a failing contract
test before implementation.

## References

- [SQLAlchemy session basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy relationship loading](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
- [Python `decimal`](https://docs.python.org/3/library/decimal.html)
- [HTTP status codes](https://www.rfc-editor.org/rfc/rfc9110.html#name-status-codes)

# Telegram transaction-message imports

## User flow

1. A linked user pastes one complete M-Pesa or Airtel Money message. `/import`
   followed by the message remains available as an explicit alternative.
2. The API parses it and returns a privacy-minimized preview.
3. The bot requires the user's description and category choice.
4. The bot shows a final preview with **Save once**, **Save & remember**, and
   **Cancel**.
5. The API reparses the source and atomically stores the transaction, provenance
   and optional user alias.
6. Temporary raw message and JWT state expire after ten minutes and are cleared
   on completion or cancellation.

The description answers “what was this for?” Provider wording only answers “what
did the payment rail report?” Keeping them separate avoids treating every payment
to the same person or supermarket as the same category.

## API

Both endpoints require the user's bearer token. The server derives ownership
from that token; neither payload accepts a user ID.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/transaction-imports/preview` | Parse without writing data |
| `POST` | `/api/transaction-imports` | Confirm and save exactly once |

Preview request:

```json
{
  "message": "COMPLETE PROVIDER MESSAGE"
}
```

Confirmation request:

```json
{
  "message": "COMPLETE PROVIDER MESSAGE",
  "description": "Weekly data bundle",
  "category": "airtime",
  "rememberAlias": "weekly data bundle"
}
```

`rememberAlias` is optional and only sent after explicit user confirmation. A
repeat import returns HTTP `409` and does not create a second transaction.

## Privacy inventory

Persisted:

- User-authored description and selected category
- Transaction amount and date
- Provider, transaction subtype and external reference
- Provider fee, currency and original timezone-aware timestamp
- Keyed message fingerprint

Not persisted:

- Raw SMS content
- Wallet balance or available limit
- Phone, account, agent or PayBill identifiers extracted only to match a format
- Telegram JWT after the short conversation finishes

Request logging must remain metadata-only; never add request bodies to Flask or
Telegram logs.

## Operations and evidence

Apply and verify only against the intended database:

```bash
FLASK_ENV=testing SQLALCHEMY_ECHO=false flask db upgrade head
FLASK_ENV=testing SQLALCHEMY_ECHO=false flask db current
```

Expected head: `f1a2b3c4d5e6`.

Run focused tests:

```bash
python -m pytest -q \
  tests/test_transaction_import_orm.py \
  tests/test_mpesa_parser.py \
  tests/test_airtel_money_parser.py \
  tests/test_fuliza_parser.py
```

Linux+ field note: local PostgreSQL commonly uses a Unix-domain socket such as
`/var/run/postgresql/.s.PGSQL.5432`. `psql -d finance_tracker_test -c '\conninfo'`
proves the database and role before migration. Socket permission failures prove
the process cannot reach PostgreSQL; they do not prove application logic failed.

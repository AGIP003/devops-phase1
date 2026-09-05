# Telegram transaction-message imports

## User flow

1. A linked user pastes one complete M-Pesa or Airtel Money message. `/import`
   followed by the message remains available as an explicit alternative.
2. The API tries a deterministic parser first. If the text looks like a
   completed provider message but no reviewed pattern matches, a minimized copy
   can use the bounded AI fallback.
3. The bot shows the provider-observed movement separately from its suggested
   reporting type. Ambiguous sends, receipts, PayBills and AI results require
   the user to choose income, expense or transfer.
4. The bot requires the user's description and category choice. Transfers use
   the dedicated `Internal Transfer` category.
5. The bot shows a final preview with **Save once**, **Save & remember**, and
   **Cancel**.
6. The API either reparses a deterministic message or verifies the AI result's
   signed, user-bound preview token. It then atomically stores the transaction,
   provenance and optional user alias.
7. Temporary raw message and JWT state expire after ten minutes and are cleared
   on completion or cancellation.

Supported Airtel Money messages include outgoing and incoming transfers,
PayBill payments, data bundles, and airtime top-ups to another subscriber. A
recipient phone number is matched but never retained; the user supplies the
human description and confirms the `Airtime` category. Airtime top-up notices
that omit a date require the user to enter `YYYY-MM-DD`; failed-transaction
notices are ignored and never stored.

Supported M-Pesa messages include outgoing and incoming transfers, PayBill,
Buy Goods, airtime, cash withdrawal, and KCB M-Pesa loan repayment notices.
Loan repayment is recorded as an expense with provider subtype
`loan_repayment`; it does not introduce a separate transaction direction.
Withdrawals are recognized as transfers. Transfers remain visible in the
transaction list but stay outside income and expense analytics. Any explicit
provider fee is still included in expenses.

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
  "type": "expense",
  "category": "airtime",
  "date": "2026-08-20",
  "rememberAlias": "weekly data bundle"
}
```

`type` is required when the preview marks classification as required. `date` is
required only when the provider message omits its transaction date.
`rememberAlias` is optional and only sent after explicit user confirmation. A
repeat import returns HTTP `409` and does not create a second transaction. An
AI-assisted preview also returns an opaque `previewToken`; clients must return
that token unchanged when the user confirms. It expires after ten minutes and
cannot be reused with a different message or by a different user.

## Parser maintenance

- Reviewed regex handles known provider formats without an AI call.
- Regex matches the stable financial record and ignores changing provider
  promotions after that record. It must not treat an advert or URL as a
  merchant or account value.
- AI is a fallback for a completed provider-looking message, not a replacement
  for deterministic parsing. It receives a minimized message with balances,
  links, phone numbers and account identifiers removed.
- Safe telemetry records only structural markers such as
  `airtel:confirmed:successful:paid_to:fee:balance`. It never records the raw
  message, reference, amount, account, phone number or merchant.
- A repeated new shape is promoted to deterministic support by adding
  anonymized regression examples, writing a reviewed parser rule, running the
  old and new tests, and deploying it. The application does not generate or
  execute regex from model output.

## Re-importing a deleted transaction

An active duplicate remains blocked. If its transaction was soft-deleted,
saving the same message again rebuilds the existing row from the new reviewed
preview. The corrected classification, category, description, merchant,
provider flow and fee replace the obsolete values, and `deleted_at` is
cleared. This preserves one provider reference and one audit trail while
letting users correct older imports through Telegram.

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
- Raw provider text inside an AI preview token (the token contains only the
  validated fields and a keyed message fingerprint)

Request logging must remain metadata-only; never add request bodies to Flask or
Telegram logs.

## Operations and evidence

Apply and verify only against the intended database:

```bash
FLASK_ENV=testing SQLALCHEMY_ECHO=false flask db upgrade head
FLASK_ENV=testing SQLALCHEMY_ECHO=false flask db current
```

Expected head: `e9b1f0a4c673`.

Run focused tests:

```bash
python -m pytest -q \
  tests/test_transaction_import_orm.py \
  tests/test_mpesa_parser.py \
  tests/test_airtel_money_parser.py \
  tests/test_fuliza_parser.py \
  tests/test_provider_import_ai.py \
  bot/tests/test_import_handler.py
```

Linux+ field note: local PostgreSQL commonly uses a Unix-domain socket such as
`/var/run/postgresql/.s.PGSQL.5432`. `psql -d finance_tracker_test -c '\conninfo'`
proves the database and role before migration. Socket permission failures prove
the process cannot reach PostgreSQL; they do not prove application logic failed.

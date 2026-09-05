# Finance analytics and grounded AI

## Decision

Moneytiqx treats PostgreSQL as the source of financial truth. The language
model may choose one operation from a small allow-list and explain its result;
it never receives database credentials, writes SQL, chooses a `user_id`, or
modifies financial records.

```text
authenticated request
        |
        v
JWT middleware derives internal user_id
        |
        v
AI selects one validated read-only operation
        |
        v
SQLAlchemy service applies user_id + deleted_at filters
        |
        v
compact aggregate JSON -> AI explanation
```

This is an application-level version of tool calling. OpenAI's Responses API
supports custom functions with typed inputs and outputs, but Moneytiqx keeps the
actual finance tools inside its own trust boundary:
<https://developers.openai.com/api/reference/cli/resources/responses/methods/create>

## Metric contract

- **Recorded spending** is the sum of owned, non-deleted expense transactions.
- **Confirmed provider fees** come from a provider message or a user's reviewed
  correction.
- **Estimated provider fees** come only from a dated, versioned rule with a
  high-confidence result. They are always shown separately.
- **Unknown fees remain unknown.** The application does not turn missing data
  into zero.
- **Total expenses** are recorded spending plus confirmed fees plus labelled
  estimates.
- **Fuliza principal is financing, not new spending.** A purchase is recorded
  when the money is spent; drawing or repaying the principal does not create a
  second expense. Explicit access or maintenance fees are expenses.
- Description-trend search matches category, description, or merchant. Category
  answers “where,” description answers “what for,” and merchant answers “who.”
  It is not specialized for a product such as airtime or sugarcane.

The reviewed catalog now supports standard non-fuel M-PESA Buy Goods plus
Airtel on-net, other-network, withdrawal and Paybill/wallet-to-bank bands.
Airtime, fuel and bank charges remain unknown when the exact source cannot
support the account and channel involved. The catalog design and source review
runbook are documented in `docs/fee_tariff_catalog.md`. Tariffs can change, so
provider messages and statements remain stronger evidence than an estimate:

- <https://www.safaricom.co.ke/personal/m-pesa/m-pesa-journey>
- <https://www.safaricom.co.ke/images/Downloads/mpesa-business-till.pdf>

## API surface

All endpoints derive ownership from the JWT and return private, non-cacheable
responses.

- `GET /api/analytics/summary?period=12-months`
- `GET /api/analytics/description-trend?query=airtime&period=month&offset=0`
- `GET /api/fees/summary`
- `GET /api/fees/tariffs`
- `POST /api/fees/estimate`
- `PATCH /api/transactions/<id>/provider-fee`
- `POST /api/provider-financing-events`
- `POST /api/ai/analytics/questions`
- `POST /api/ai/analytics/weekly-summary`

Supported search windows are calendar week (Monday to Sunday), calendar month
(daily bars), calendar year (monthly bars), and all recorded history. Negative
offsets select earlier calendar periods; `month&offset=-1` is last month. The
fee-edit endpoint does not
allow a provider-reported fee to be overwritten. Editing an estimate changes
its source to `user_confirmed` while retaining `original_estimated_fee` and the
tariff version for auditability.

The weekly endpoint is an on-demand preview. Automatic Telegram or email
delivery is deliberately absent until the user has an explicit opt-in setting
and a reviewed scheduler/worker deployment. Previewing is not consent to send.
The preview uses the current and previous calendar week plus a compact 30-day
planning context containing goals, debts, commitments, upcoming payments and
deterministic signals. With no weekly transactions it still reports recorded
plans, while clearly saying that spending comparisons are unavailable.

## Privacy and failure behaviour

- Raw provider SMS messages are parsed in memory and are not persisted.
- Stored provenance uses an HMAC fingerprint plus the minimum parsed fields.
- Wallet balances, phone numbers, account numbers and raw transaction rows are
  not sent to the model for analytics answers. A bounded search may send its top
  matching description and merchant aggregates because those labels are needed
  to answer “what?” and “who?”; unrelated history is excluded.
- The AI request uses an opaque HMAC safety identifier, `store=False`, strict
  Pydantic output schemas, output-token limits and per-user cost/rate limits.
- A finance question reserves more of the daily AI budget than a one-call bot
  reply because it performs a validated planning call and an explanation call.
- If OpenAI is unavailable or the quota is exhausted, deterministic charts and
  search continue to work; only the narrative response fails.
- Empty search results mean “no matching recorded transactions,” not “the user
  never made that purchase.”

## Operations

Apply the migration through Alembic, never `db.create_all()` in production:

```bash
FLASK_ENV=testing flask db upgrade head
```

Preview fee backfill first. The command is dry-run by default:

```bash
FLASK_ENV=development python -m scripts.backfill_provider_fees
FLASK_ENV=development python -m scripts.backfill_provider_fees --apply
```

The script prints its database target and candidate evidence. Review the dry
run before `--apply`; do not point it at Railway merely to experiment.

## Verification checklist

- Search includes description and merchant matches.
- Search excludes other users and soft-deleted rows.
- Provider-reported fees cannot be manually overwritten.
- Estimated fees preserve their original value after user confirmation.
- Fee backfill is dry-run by default and idempotent when applied.
- Fuliza duplicates are rejected and principal is not added to expenses.
- AI executes only a validated operation with the authenticated user ID.
- Telegram uses a separate financing confirmation flow and clears the raw
  message and short-lived JWT from conversation memory afterward.
- Alembic upgrade, downgrade and re-upgrade work on the guarded test database.
- Backend, bot and frontend tests pass, followed by the frontend production
  build.

## Deferred work

- A complete dated tariff registry with source snapshots and effective dates.
- User opt-in, delivery timezone and scheduler for recurring weekly summaries.
- Foreign-currency normalization with the original amount and exchange-rate
  provenance retained.
- A user-facing correction history rather than only the preserved original
  estimate.

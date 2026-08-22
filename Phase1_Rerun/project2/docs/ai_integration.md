# AI-Assisted Transaction and Receipt Parsing

## Purpose

AI is an optional extraction assistant. It may suggest structured fields, but
it does not own authorization, validation, currency conversion, or database
writes. Users review and confirm all financial records before they are saved.

## Trust boundaries

```text
Telegram or web client
        |
        | authenticated request
        v
Flask API
  - validates text or image bytes
  - applies per-user rate limits
  - reserves daily AI budget in PostgreSQL
        |
        | store=false, structured schema
        v
OpenAI Responses API
        |
        | untrusted structured suggestion
        v
Pydantic and canonical-category validation
        |
        | preview only
        v
Human description, choices and final confirmation
        |
        v
Existing transaction API and ownership checks
```

The OpenAI key remains in the Flask backend. The Telegram bot never receives
it. Receipt bytes and raw financial descriptions are not written to logs or to
the AI usage table.

## Endpoints

- `POST /api/ai/transactions/preview` accepts JSON containing `text`.
- `POST /api/ai/receipts/preview` accepts a multipart `image`.

Both endpoints require the existing JWT, return `Cache-Control: private,
no-store`, and return structured previews rather than saved transactions.

## Receipt workflow

1. Telegram downloads the largest image variant.
2. Pillow verifies the image type, integrity, byte size and pixel count.
3. The authenticated backend extracts a structured receipt preview.
4. The user supplies a description.
5. The user supplies a missing date when necessary.
6. The user chooses the category and payment method.
7. A final button explicitly saves or cancels the transaction.

Foreign-currency receipts remain preview-only until transactions can persist
their original currency and conversion evidence. Treating a USD amount as KES
would corrupt balances and analytics.

## Cost controls

Three controls serve different purposes:

1. Flask rate limits reduce repeated requests from one authenticated user.
2. PostgreSQL holds one aggregate `ai_daily_usage` row per UTC day so every
   Gunicorn worker shares the same budget state.
3. The OpenAI project budget is the final provider-side financial guardrail.

Before a provider call, the application reserves a conservative amount:

- transaction extraction: `AI_TRANSACTION_RESERVATION_USD`, default `$0.005`;
- receipt extraction: `AI_RECEIPT_RESERVATION_USD`, default `$0.05`.

After a successful response, the reservation is replaced by the token-based
estimate. If provider usage is unknown because the request failed, the full
reservation remains counted. This intentionally prefers temporarily refusing
AI over unexpectedly exceeding the application budget.

The local estimate is operational telemetry, not an invoice. OpenAI's Usage
and Costs records remain authoritative.

## Configuration

```text
OPENAI_API_KEY
OPENAI_TRANSACTION_MODEL=gpt-5.6-luna
AI_FALLBACK_ENABLED=true
AI_DAILY_BUDGET_USD=0.25
AI_TRANSACTION_RESERVATION_USD=0.005
AI_RECEIPT_RESERVATION_USD=0.05
AI_REQUEST_TIMEOUT_SECONDS=12
AI_TRANSACTION_MAX_OUTPUT_TOKENS=500
AI_RECEIPT_MAX_OUTPUT_TOKENS=1600
AI_REASONING_EFFORT=low
```

## Testing

Unit tests mock the OpenAI client, so routine tests spend no money and require
no API key. PostgreSQL integration tests prove that concurrent reservations
cannot silently pass the daily ceiling and that completion/failure accounting
is reconciled correctly.

```bash
./venv/bin/python -m pytest -v tests/test_ai_services.py
./venv/bin/python -m pytest -v tests/test_image_validation.py
./venv/bin/python -m pytest -v tests/test_ai_budget.py
./venv/bin/python -m pytest -v bot/tests/test_receipt_handler.py
```

Before deployment, apply migration `b6d8e4a19c20` through the existing
`flask db upgrade` pre-deploy command. Never use `db.create_all()` or
`db.drop_all()` against Railway.

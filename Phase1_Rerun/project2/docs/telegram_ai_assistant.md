# Telegram AI assistant

## Purpose

The Telegram bot uses AI as a bounded language layer, not as the source of
financial truth. Commands, database calculations, provider-message parsing and
database writes remain application responsibilities.

Message routing follows this order:

1. Telegram commands use their existing deterministic handlers.
2. M-Pesa and Airtel Money messages use the strict regex import pipeline. This
   preserves provider references and duplicate detection.
3. Receipt photos use the validated image and receipt-preview pipeline.
4. Other text is sent to the bounded Telegram assistant.

The assistant can classify a message as a transaction, balance request, bot
help question, general finance-education question or unsupported request. A
balance intent invokes the existing database-backed handler. An AI transaction
is only a preview: the user can change category or payment method and must press
Save before the backend receives a create request.

## Trust and privacy boundaries

- The backend derives the user from the JWT; Telegram never supplies a database
  user ID to the AI endpoint.
- Model output must satisfy `TelegramAssistantResponse` before the bot uses it.
- AI cannot call database functions or save, edit or delete records directly.
- A stable HMAC safety identifier is sent instead of the internal user ID.
- Requests use `store=False` and do not include passwords, JWTs, provider PINs,
  transaction history or account numbers.
- Pending AI transactions and their short-lived JWT expire after ten minutes
  and are cleared after save or cancellation.
- Foreign-currency previews are not silently stored as KES.

## Reliability and cost controls

`POST /api/ai/telegram/respond` is authenticated and rate limited. Every call
reserves part of the shared daily AI budget before contacting the provider. The
reservation is replaced with measured token cost after a successful response.

When OpenAI is unavailable, deterministic provider imports and commands still
work. Common balance wording also falls back to the exact balance handler.

Required production configuration:

```text
OPENAI_API_KEY=<server-side project key>
OPENAI_TRANSACTION_MODEL=gpt-5.6-luna
AI_FALLBACK_ENABLED=true
AI_DAILY_BUDGET_USD=0.03
AI_ASSISTANT_RESERVATION_USD=0.002
AI_ASSISTANT_MAX_OUTPUT_TOKENS=450
```

An API key alone does not provide quota. The OpenAI project must also have
usable API billing credit and an appropriate project spending limit.

## Verification

Backend service tests fake the provider response and verify schema validation,
`store=False`, the opaque safety identifier and budget-before-provider order.
Bot tests prove that questions receive a response, AI transactions are not
saved before confirmation, temporary state is cleared, and balance remains
available during an AI outage.

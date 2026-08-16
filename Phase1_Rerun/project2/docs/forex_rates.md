# Forex rates: operation and API contract

## Data flow

`Browser -> MoneyTiq API -> PostgreSQL cache -> Frankfurter -> CBK provider data`

The frontend never calls Frankfurter directly. MoneyTiq requests one normalized
set with `base=KES`, the supported quote currencies, and `providers=CBK`.
Routine tests replace this external boundary with deterministic fakes.

## API

Authenticated request:

```http
GET /api/forex/rates
Authorization: Bearer <access-token>
```

Successful response:

```json
{
  "base": "KES",
  "provider": "CBK",
  "source": "Frankfurter",
  "rateDate": "2026-08-14",
  "fetchedAt": "2026-08-16T10:00:00+00:00",
  "stale": false,
  "rates": {
    "KES": "1",
    "AED": "0.02843",
    "AUD": "0.01095",
    "BIF": "23.13",
    "CAD": "0.01077",
    "CHF": "0.00629",
    "CNY": "0.05219",
    "DKK": "0.05013",
    "EUR": "0.0067",
    "GBP": "0.00573",
    "HKD": "0.06072",
    "INR": "0.74074",
    "JPY": "1.2327",
    "NOK": "0.07348",
    "RWF": "11.36",
    "SAR": "0.02905",
    "SEK": "0.07391",
    "SGD": "0.0099",
    "TZS": "20.46",
    "UGX": "28.7",
    "USD": "0.00774",
    "ZAR": "0.12531"
  }
}
```

Rates are strings so the API does not silently introduce binary floating-point
rounding. JavaScript converts them to `Number` only for display formatting.

Every rate is expressed as quote-currency units per one KES. The browser can
therefore calculate a cross-rate without another provider request:

```text
converted amount = amount × target KES rate ÷ source KES rate
```

The converter is for indicative display only, not accounting entries or
executable trading quotes.

`stale: true` means provider refresh failed and the response is a previous,
validated database snapshot. A `503` means neither the provider nor a complete
cache was available.

## Configuration

Defaults are suitable for deployment; override only after review:

- `FOREX_API_BASE_URL=https://api.frankfurter.dev/v2`
- `FOREX_PROVIDER=CBK`
- `FOREX_CACHE_TTL_SECONDS=21600`
- `FOREX_CONNECT_TIMEOUT_SECONDS=3`
- `FOREX_READ_TIMEOUT_SECONDS=10`

No forex API key is required. Never log authorization headers or complete
environment-variable output while diagnosing the feature.

## Verification

```bash
FLASK_ENV=testing SQLALCHEMY_ECHO=false ./venv/bin/flask db current
./venv/bin/python -m pytest -v tests/test_forex.py
cd tracker-frontend
npm test -- --run src/pages/Forex.test.jsx
npm run lint
npm run build
```

The backend tests prove external-response validation, Decimal parsing, HTML
rejection, complete-set persistence, fresh-cache reuse, stale fallback,
no-cache failure, authentication, and serialization.

## Failure diagnosis

Check the MoneyTiq endpoint first; do not begin by repeatedly calling the
provider:

```bash
curl -i --max-time 15 \
  -H "Authorization: Bearer $MONEYTIQ_ACCESS_TOKEN" \
  "$MONEYTIQ_API_URL/api/forex/rates"
```

Interpretation:

- `200`, `stale=false`: current validated cache/provider result.
- `200`, `stale=true`: graceful degradation; investigate provider reachability.
- `401`: access token problem, not a forex-provider problem.
- `503`: no complete cached set exists and refresh failed.

`curl` exit status proves transport success or failure; it does not prove the
response contains valid rates. Always inspect HTTP status, `Content-Type`, JSON
shape, `rateDate`, and `stale`.

# ADR 0001: Forex provider and last-known-good cache

Status: Accepted
Date: 2026-08-16

## Context

MoneyTiq needs daily KES reference rates for USD, EUR, GBP, UGX, and TZS.
Direct CBK automation currently encounters a Sucuri JavaScript challenge, while
the historical CSV available through the browser is stale and inconsistent.
The application must continue displaying its last validated rates during an
upstream outage and runs multiple Gunicorn worker processes on Railway.

These rates are indicative display rates. They are not executable trading
quotes and must not be represented as real-time prices.

## Options considered

1. Scrape CBK's undocumented WordPress/DataTables endpoint directly. This is
   closest to the source but is blocked by a WAF, undocumented, and expensive
   to maintain.
2. Call Frankfurter's documented v2 API with `providers=CBK`. This retains CBK
   attribution while providing a stable JSON contract and no-key public API.
3. Call Frankfurter directly from every browser. This is simple but removes
   central validation, multiplies provider traffic, and cannot provide a shared
   durable fallback.
4. Cache with Redis and refresh from a scheduler. This scales well but adds a
   service and operating burden that the current application does not need.

## Decision

The Flask backend calls Frankfurter v2 with the provider pinned to `CBK`. It
normalizes the response to a KES base, strictly validates the complete currency
set, and persists only a complete valid set in PostgreSQL. The authenticated
`GET /api/forex/rates` endpoint serves that data to the frontend.

PostgreSQL is the shared last-known-good cache. A six-hour fetch TTL limits
provider traffic. When refresh fails, a complete previous set is returned with
`stale: true`. If no valid cache exists, the endpoint returns `503`.

## Reasons

- PostgreSQL is already deployed, backed up, and shared by all workers.
- An in-process cache would be different in each worker and disappear at restart.
- Frankfurter documents CBK coverage and provides already normalized KES pairs.
- Validation before persistence prevents HTML/error pages, partial sets,
  duplicates, invalid dates, or non-positive values replacing good data.
- Authentication prevents the Railway deployment becoming an unauthenticated
  public proxy for the upstream API.

## Consequences

- MoneyTiq depends on Frankfurter availability when the cache needs refreshing.
- The first request after the TTL can wait for the upstream timeout.
- Several workers can refresh simultaneously after expiry; the unique database
  constraint and upsert keep storage correct, but do not prevent duplicate
  upstream requests.
- The UI must attribute Frankfurter and describe the figures as daily indicative
  reference rates.

## Revisit when

- Provider latency materially affects the request SLO.
- Duplicate refreshes approach upstream rate limits.
- MoneyTiq already operates Redis and a background scheduler.
- Accounting or regulatory use requires a different authoritative rate contract.
- Frankfurter's CBK coverage, license, API contract, or availability changes.

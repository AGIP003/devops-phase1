# Pytest suite markers

The test suite uses markers as independent dependency and confidence labels.
A test may carry more than one marker. For example, an authenticated AI route
test is `integration`, `external`, and may also be `critical`.

## Marker contracts

- `no_database`: the test does not query or clean PostgreSQL. The autouse
  cleanup fixture skips database work for this test.
- `integration`: the test initializes Flask and uses the isolated PostgreSQL
  test database. This marker is added automatically to every collected test
  that is not marked `no_database`, matching the cleanup fixture's behaviour.
- `external`: the test exercises an external-provider boundary through a fake,
  stub, or monkeypatch. Routine automated tests must not call live OpenAI,
  Google, Telegram, forex, or market-data services.
- `critical`: a deliberately small API confidence spine. CI can run this first
  to distinguish a fundamental application failure from a failure in the
  wider suite.

`--strict-markers` is enabled in `pytest.ini`, so a misspelled or undeclared
marker fails collection instead of being silently ignored.

## Useful commands

```bash
# Fast API confidence spine
./venv/bin/python -m pytest -m critical -v

# Flask + PostgreSQL integration tests
./venv/bin/python -m pytest -m integration -v

# Mocked external-provider boundary tests
./venv/bin/python -m pytest -m external -v

# Tests that require neither PostgreSQL nor a live provider
./venv/bin/python -m pytest -m no_database -v

# Pure mocked-boundary tests, without PostgreSQL
./venv/bin/python -m pytest -m "external and no_database" -v

# Complete regression suite
./venv/bin/python -m pytest -v
```

Marker selection is not a replacement for the complete suite. The critical
phase gives fast diagnostic feedback; the full suite remains the merge gate.

## Critical transaction guarantees

The critical spine explicitly proves that:

- registration produces distinct authenticated users;
- an authenticated user can create a transaction;
- transaction listing succeeds and returns only the authenticated user's rows;
- another authenticated user cannot read, update, or delete the transaction;
- budget ownership remains enforced;
- analytics aggregates owned finance records and rejects invalid or
  unauthenticated requests;
- profile changes persist for the authenticated account and login continues to
  issue a token;
- Google sign-in retains its identity/idempotency contract;
- a Telegram session token is accepted by the normal authentication middleware;
- mocked AI success and provider-failure responses retain their safe API
  contracts.

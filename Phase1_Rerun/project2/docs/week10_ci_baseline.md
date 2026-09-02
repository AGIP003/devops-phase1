# Week 10 CI Testing Baseline

Date: 2026-08-31

## Purpose

This document records the pre-CI testing contract for Moneytiq. The
baseline represents tests that must be reproducible on a clean Linux
runner with an isolated PostgreSQL database and no production
credentials.

## Environment

- Local platform: WSL Ubuntu
- Local Python: 3.12.3
- Docker/production Python target: 3.13
- pytest: 8.2.2
- pytest-cov: 5.0.0
- Database engine: PostgreSQL
- Test database: `finance_tracker_test`
- Local database transport: Unix socket
- Production credentials required by tests: No

## Test results

| Selection | Result | Duration |
|---|---:|---:|
| Critical confidence spine | 12 passed, 183 deselected | 17.05s |
| PostgreSQL integration | 91 passed, 104 deselected | 102.01s |
| Complete suite with coverage | 195 passed | 112.81s |

The baseline increased from 193 to 195 tests because two explicit API
tests were added:

- Authenticated transaction creation
- Authenticated, owner-isolated transaction listing

## Critical API behaviours

The critical test selection covers:

- Password and Google authentication
- `POST /api/transactions`
- `GET /api/transactions`
- Transaction ownership enforcement
- `GET /api/analytics/summary`
- Invalid and unauthenticated analytics requests
- Budget ownership
- Telegram session authentication
- AI validated responses
- AI provider failure handling

The critical subset provides fast diagnostic feedback. The complete
195-test suite remains the merge gate.

## Database isolation contract

Tests create the Flask application with `create_app("testing")`.

Database protection includes:

1. `TEST_DATABASE_URL` is required.
2. `TEST_DATABASE_URL` must differ from `DATABASE_URL`.
3. The database name must end in `_test`.
4. PostgreSQL `current_database()` is checked before destructive cleanup.
5. Tables are truncated before and after database tests.
6. Tests use `TRUNCATE ... RESTART IDENTITY CASCADE`.
7. Alembic migrations must run before pytest; tests do not create the
   schema with `db.create_all()`.

## External-service isolation

- `TestingConfig` removes the OpenAI API key.
- AI functionality is disabled by default in testing.
- Tests that exercise AI explicitly enable it and inject fake provider
  implementations.
- OpenAI success, malformed response and provider failure paths are
  tested without paid calls.
- Google transport failure is mocked.
- Telegram bot/backend calls are mocked at service boundaries.
- Tests do not depend on live Telegram availability.

## Coverage baseline

Coverage measures `app` and `bot`, excluding test source and
`app/test_email.py`.

- Statements: 6,637
- Missed statements: 1,830
- Statement coverage: 72.4%

This is a diagnostic baseline, not a claim that the application is
72.4% correct. The initial CI coverage floor should be set below the
measured baseline so regressions are caught without encouraging
low-value tests purely to increase a percentage.

## Priority coverage gaps

1. `bot/api_client.py` — 23.4%
2. `app/services/quotation_service.py` — 40.1%
3. `app/services/user_service.py` — 54.2%
4. `app/services/transaction_service.py` — 64.1%
5. `app/services/telegram_files_service.py` — 40.0%

Startup-only modules such as `bot/main.py` will primarily be validated
through container startup and post-deployment smoke testing.

## CI requirements for Day 2

A clean CI runner must:

1. Use the repository working directory `Phase1_Rerun/project2`.
2. Install a declared Python version and declared dependencies.
3. Start disposable PostgreSQL.
4. Wait for PostgreSQL readiness.
5. provide CI-only `TEST_DATABASE_URL` and fake test configuration.
6. Run Alembic migrations.
7. Run all 195 tests.
8. Generate coverage output.
9. Preserve test and coverage evidence.

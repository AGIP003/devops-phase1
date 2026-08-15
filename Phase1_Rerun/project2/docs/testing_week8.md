# Week 8 PostgreSQL Testing Evidence

## Purpose

Day 6 introduced isolated PostgreSQL integration tests for the SQLAlchemy ORM data layer. The tests protect ownership rules, soft-delete behaviour, transaction rollback, and Telegram persistence.

## Test database safety

Tests use `TEST_DATABASE_URL` and refuse to run unless:

- it differs from `DATABASE_URL`;
- its database name ends in `_test`;
- the connected PostgreSQL database reports a name ending in `_test`.

Before and after every database test, the fixture truncates the test tables and resets their identity sequences. Development and Railway data are not cleaned by pytest.

## Fixtures

- `app`: creates one Flask application in testing mode.
- `clean_database`: provides repeatable database cleanup around every test.
- `client`: sends requests through Flask without starting a network server.
- `register_user`: creates distinct authenticated users for ownership tests.
- `payment_method`: seeds required payment-method reference data.

## Behaviours proved

- A user cannot read, update, or delete another user’s transaction.
- The rightful owner can still access the unchanged transaction.
- Soft-deleted transactions disappear from active API queries while remaining stored with `deleted_at`.
- A failed transaction rolls back its category and transaction together.
- The SQLAlchemy session remains usable after rollback.
- A user cannot view, modify, or delete another user’s budget data.
- Telegram link tokens are single-use and expire correctly.
- Telegram preferences persist through PostgreSQL JSONB.
- Existing Telegram transaction-parser tests remain passing.

## Time handling

All persistent timestamps now use timezone-aware UTC values and PostgreSQL `timestamp with time zone`.

Migration `9f3b1c7a2d4e`:

- interprets existing naive timestamps as UTC;
- converts 15 timestamp columns to timezone-aware storage;
- supports a reverse migration to naive UTC;
- removes Python 3.12 `datetime.utcnow()` warnings.

## Evidence

- Database integration tests: 8 passed.
- Complete suite: 15 passed.
- Complete suite passed in normal and deliberately changed order.
- Coverage command reported 49% across the entire `app` package.
- The retained historical `app/db.py` contributes 418 uncovered statements and is not imported by active application code.
- Models and serializers exercised by these tests reported 100% coverage.
- Alembic reported no model/schema changes after the timezone migration.
- The timezone migration passed upgrade, downgrade, and re-upgrade checks on `finance_tracker_test`.
- The warning-visible test run completed with no `datetime.utcnow()` warnings.

## Commands

```bash
./venv/bin/python -m pytest -v
./venv/bin/python -m pytest --cov=app --cov-report=term-missing tests/
FLASK_ENV=testing ./venv/bin/flask db current
FLASK_ENV=testing ./venv/bin/flask db check

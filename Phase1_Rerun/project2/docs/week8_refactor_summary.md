# Week 8 SQLAlchemy ORM Refactor

## Executive summary

Week 8 replaced the Finance Tracker's active raw-`psycopg2` data layer with
SQLAlchemy ORM services, established a reproducible Alembic migration history,
added isolated PostgreSQL integration tests, converted persistent timestamps to
timezone-aware UTC, and validated the result in Railway production.

The refactor preserved the frontend-facing transaction, budget, authentication,
and Telegram contracts for the workflows exercised. It also closed a critical
authorization class: user-owned records are now selected with both resource ID
and authenticated `user_id`, so knowing another row's ID is not enough to read,
update, or delete it.

The original implementation is retained under `archive/` for learning history.
It is not imported by the running application.

## Objectives and outcome

| Objective | Outcome |
| --- | --- |
| Replace active raw SQL/`psycopg2` usage | Complete for application and bot runtime paths |
| Create a reproducible schema history | Complete: one linear Alembic chain from `base` to head |
| Preserve API compatibility | Verified for exercised web and Telegram workflows |
| Prevent cross-user data access | Covered by service design and integration tests |
| Implement transaction soft delete | Complete and production-verified |
| Move timestamps to aware UTC | Complete across 15 columns |
| Demonstrate N+1 behaviour and inspect indexes | Measured; no speculative index added |
| Build safe PostgreSQL tests | Complete with layered test-database guards |
| Validate production deployment | Complete, including backup, migration, and smoke tests |

## Architecture

### Before

Routes called a large `app/db.py` module containing connection management, SQL
strings, cursor execution, commits, rollbacks, and row-shape assumptions. The
module mixed persistence concerns from transactions, users, budgets, Telegram,
and authentication.

### After

```text
HTTP request
    |
    v
Flask route ---------------------- authentication + HTTP validation/status
    |
    v
Domain service ------------------- ownership query + use-case transaction
    |
    v
SQLAlchemy model/session ---------- relationships + unit of work
    |
    v
PostgreSQL
    |
    v
Explicit serializer -------------- stable frontend JSON contract
```

Responsibilities are now separated:

- `app/routes.py`, `app/auth_routes.py`, and `app/telegram_routes.py` own HTTP
  input, authentication, and status codes;
- `app/services/` owns business operations, ownership filters, commits, and
  rollback;
- `app/models/` owns mappings, relationships, constraints, and domain helpers;
- `app/serializers.py` owns the public transaction and budget JSON shapes;
- `migrations/versions/` owns schema evolution;
- `tests/` owns PostgreSQL integration evidence;
- `archive/legacy_psycopg2_db.py` preserves the earlier approach without being
  part of runtime code.

## Important engineering decisions

### One database URL per running environment

Runtime persistence now uses SQLAlchemy's configured
`SQLALCHEMY_DATABASE_URI`, resolved from `DATABASE_URL`. Development and
production select different databases by providing different environment
values, not by branching database code. Missing configuration fails at startup
instead of silently switching to an in-memory SQLite database.

Tests resolve `TEST_DATABASE_URL` only when `create_app("testing")` is called.
This keeps ordinary development independent from test configuration and makes
the test database choice explicit.

### One SQLAlchemy metadata graph

All active models share the Flask-SQLAlchemy declarative base and are imported
during application creation. Alembic therefore compares the real model table
graph to the connected database instead of seeing empty or competing metadata.

### Ownership belongs in the query

User-scoped services select using both identifiers:

```python
Transaction.id == transaction_id
Transaction.user_id == user_id
```

The same principle applies to budgets and budget items. Authentication answers
“who is calling?” Ownership filtering answers “may that caller act on this
specific row?” They solve different security problems.

HTTP 404 is returned for both absent and foreign-owned records. This prevents
the endpoint from becoming a resource-existence oracle.

### Services own database transactions

A multi-step use case either commits completely or rolls back completely.
Creating a category and then failing to create its transaction does not leave
an orphan category. Every write service rolls the SQLAlchemy session back before
re-raising an exception, which also makes the request-scoped session usable
after a failed flush or commit.

### Explicit serializers protect the API

The ORM is not serialized automatically. Explicit serializers:

- exclude private columns such as `password_hash`;
- convert dates and timestamps to ISO 8601;
- preserve transaction money as decimal strings;
- flatten category and payment-method relationships to their existing names;
- stabilize budget-item ordering;
- prevent internal schema changes from leaking into the frontend contract.

### Relationship loading is deliberate

Transaction reads use `selectinload()` for category and payment method. Budget
reads use `selectinload()` for items. This avoids hidden per-row lazy queries
when serializers traverse relationships while keeping collection loading
predictable.

### Time means an instant

Python now creates persistent timestamps with `datetime.now(UTC)`, ORM columns
use `DateTime(timezone=True)`, and PostgreSQL stores them as `timestamp with time
zone`. Migration `9f3b1c7a2d4e` interprets prior naive values under the
application's established naive-UTC convention.

This removed Python 3.12 `datetime.utcnow()` deprecation warnings and prevents
comparisons between naive and aware datetimes in expiry and soft-delete logic.

## Schema history

```text
<base>
  -> 203a99a228f5  baseline schema
  -> 731c6bd75249  deleted_at + budget list tables
  -> 9f3b1c7a2d4e  timezone-aware UTC timestamps
```

The chain has one base and one head. It passed:

- upgrade from an empty `finance_tracker_test` database to head;
- downgrade from head to base;
- re-upgrade from base to head;
- `flask db check` against ORM metadata;
- the complete test suite after reconstruction.

The baseline creates referenced tables before dependent foreign keys, creates
indexes after tables, and drops objects in reverse dependency order.

## Domain changes

### Transactions

- CRUD moved to `transaction_service.py`.
- Category and payment method are real ORM relationships.
- Queries are scoped by authenticated user.
- Default lists exclude `deleted_at IS NOT NULL` rows.
- Delete is now a soft delete.
- Category creation and transaction creation share one unit of work.
- Active lists eager-load serializer relationships and order newest dates first.

### Budgets

- Budget and item CRUD moved to `budget_service.py`.
- Items are managed as an owned collection with deterministic positions.
- Item authorization is derived through the parent budget's `user_id`.
- Budget/item writes commit or roll back as one operation.
- Budget reads avoid caching in shared browser/proxy storage.

### Authentication and users

- User lookup, creation, password updates, and deletion moved to ORM services.
- Duplicate user conflicts map to HTTP 409.
- JWT payload and public user response shapes remain stable.
- Password hashes remain server-side only.

### Telegram

- Link tokens, account links, sessions, and preferences moved to ORM services.
- Tokens are expiring and single-use.
- Preferences use the existing PostgreSQL JSONB design.
- Bot authentication and rate limits remain at the HTTP boundary.
- Existing parser tests were retained rather than replacing the bot's tested
  language behaviour.

## Query and index review

The transaction-list path was measured before declaring the N+1 problem fixed.
With only one active transaction, lazy and eager versions both issued three
queries, so that dataset could not demonstrate scaling. The important expected
shape is:

- lazy loading: the initial transaction query plus queries triggered for
  distinct related rows;
- current eager loading: one transaction query, one category query, and one
  payment-method query.

PostgreSQL's measured plan for the active user/date query used
`idx_transactions_user_date` through a bitmap index scan. Execution took
0.646 ms on the small local dataset and sorting used 25 KiB.

No index was added because the existing composite index was already selected.
A partial index for active transactions is a measurement-driven option only if
row volume, soft-deleted-row ratio, latency, buffers, or CPU later justify it.
This avoids the write cost and storage cost of an index without evidence.

See [performance_week8.md](performance_week8.md) for the captured plan summary.

## Test strategy and evidence

Tests run against PostgreSQL rather than substituting SQLite, because the
application relies on PostgreSQL behaviour including JSONB, partial indexes,
foreign keys, and timestamp semantics.

The fixture stack provides:

- a session-scoped testing Flask application;
- a Flask test client;
- destructive cleanup only after three test-database checks;
- distinct authenticated user creation;
- required payment-method reference data.

Eight database integration tests prove:

- transaction read/update/delete ownership;
- rightful-owner access after an intrusion attempt;
- soft-delete visibility and persistence;
- rollback of partial transaction creation and session recovery;
- budget and item ownership;
- Telegram token single use;
- Telegram token expiry;
- Telegram JSONB preference round trips.

Seven existing bot parser tests bring the complete suite to 15 passing tests.
The suite also passed in a deliberately changed order, reducing the chance that
tests depend on leaked database state.

A historical coverage run reported 49% over the whole `app` package while the
418-line raw SQL module was still counted as active source. That module has
since moved to `archive/`; the old percentage must not be presented as current
active-code coverage without rerunning coverage.

See [testing_week8.md](testing_week8.md) for test commands and detailed evidence.

## Production release evidence

Before deployment:

- Railway PostgreSQL reported version 18.4 and Alembic revision
  `731c6bd75249`;
- a PostgreSQL 18.6 client created a 39 KiB custom-format backup;
- `pg_restore --list` read 94 table-of-contents entries;
- the backup's SHA-256 checksum passed;
- Railway's application-service pre-deploy command was set to
  `flask db upgrade`.

After the feature branch was merged into the `main` branch watched by Railway:

- pre-deploy migration completed;
- Gunicorn 26 started three workers;
- application, Auth, and Telegram startup logs were healthy;
- Alembic reported `9f3b1c7a2d4e`;
- all 15 migrated columns reported `timestamp with time zone`;
- login, dashboard reads, transaction CRUD/soft delete, budget CRUD/item state,
  Telegram status/preferences, bot balance, and bot transaction entry worked.

The controlled transaction was refreshed after update and queried directly
after deletion, proving both persistence of the new amount and preservation of
the soft-deleted row.

Operational instructions and rollback boundaries are in
[week8_migration_runbook.md](week8_migration_runbook.md).

## Commits

| Commit | Purpose |
| --- | --- |
| `e568a12` | Establish reproducible Alembic baseline |
| `79d15d2` | Add NSE frontend mock (separate feature detour; no NSE backend) |
| `0d89891` | Refactor transaction and budget CRUD to SQLAlchemy ORM |
| `6fbd2c9` | Measure ORM loading and document transaction query plan |
| `173914d` | Complete PostgreSQL integration testing and aware-UTC migration |
| `0408be9` | Archive the inactive legacy psycopg2 data layer |

## Honest boundaries

The following are not claimed as complete:

- The backup is checksum-verified and structurally inspected, but has not yet
  passed a full restore drill into PostgreSQL 18.
- The integration suite focuses on the highest-risk ownership, rollback,
  soft-delete, and Telegram behaviours; it is not exhaustive API coverage.
- The 49% coverage number is historical and should be rerun after the archive
  move before setting a coverage gate.
- The one-row N+1 measurement cannot demonstrate growth; a larger controlled
  dataset is needed for numeric before/after scaling evidence.
- The NSE experience is frontend-only and must not be described as a live
  market-data integration.

These boundaries are documented so future work begins from facts instead of
inflated completion claims.

## Engineering lessons retained

1. Model metadata is the schema Alembic expects; the database is the schema
   Alembic observes. Both must point to the same model graph and target database.
2. Authentication without row ownership is insufficient authorization.
3. A foreign key protects referential integrity; it does not grant access.
4. Compilation proves syntax/import viability, not correct behaviour.
5. A commit protects history locally; a push copies it to the remote.
6. A migration passing locally is evidence, not production validation.
7. A backup that has never been restored is an unproven recovery hypothesis.
8. Add indexes because query plans and workload data justify them, not because
   a column appears in a filter.
9. API serializers are compatibility boundaries, not formatting conveniences.
10. Production work is complete only when schema, application behaviour,
    observability, and recovery evidence agree.

## References

- [SQLAlchemy ORM quick start](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [SQLAlchemy session basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy relationship loading](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
- [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [PostgreSQL date/time types](https://www.postgresql.org/docs/current/datatype-datetime.html)
- [Python aware and naive datetime objects](https://docs.python.org/3/library/datetime.html#aware-and-naive-objects)
- [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [Railway pre-deploy commands](https://docs.railway.com/deployments/pre-deploy-command)
- [PostgreSQL backup and restore](https://www.postgresql.org/docs/18/backup.html)

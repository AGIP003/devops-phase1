# Week 8 Database Migration Runbook

This runbook describes how to release, verify, and reverse the Week 8
SQLAlchemy/Alembic changes without treating the production database as a test
environment.

| Field | Value |
| --- | --- |
| Application | Finance Tracker |
| Production platform | Railway |
| Application service | `devops-phase1` |
| Database service | `Postgres` |
| Deployment branch | `main` |
| Current Alembic head | `9f3b1c7a2d4e` |
| Last validated | 2026-08-14 |

## Safety invariants

These rules are release blockers, not suggestions:

1. Never run `db.drop_all()`, `DROP DATABASE`, or test cleanup against Railway.
2. Never run pytest unless `TEST_DATABASE_URL` points to a separate PostgreSQL
   database whose name ends in `_test`.
3. Take and inspect a production backup before a destructive or type-changing
   migration.
4. Use Alembic for schema changes. Do not edit the production schema manually.
5. Confirm the target database and current revision before upgrade or downgrade.
6. Do not put database URLs, access tokens, or backup files in Git.
7. A successful migration is not the end of the release: verify the revision,
   schema, application health, and user-visible behaviour.

## Migration chain

```text
<base>
  -> 203a99a228f5  baseline application schema
  -> 731c6bd75249  transaction soft delete and budget tables
  -> 9f3b1c7a2d4e  timezone-aware UTC timestamps
```

Migration `9f3b1c7a2d4e` changes 15 columns from `timestamp without time
zone` to `timestamp with time zone`. Existing values are interpreted as UTC
with PostgreSQL's `AT TIME ZONE 'UTC'` expression. Its downgrade converts the
same instants back to naive UTC values.

## Environment map

| Environment | Configuration | Purpose | Destructive cleanup allowed? |
| --- | --- | --- | --- |
| Local development | `DATABASE_URL` | Manual development | No automatic cleanup |
| Local testing | `TEST_DATABASE_URL` | Repeatable pytest runs | Yes, after all safety guards pass |
| Railway production | Railway `DATABASE_URL` | Real application data | Never |

The application has three independent test-database guards:

- `TEST_DATABASE_URL` must be present;
- it must differ from `DATABASE_URL` and its parsed database name must end in
  `_test`;
- the live PostgreSQL connection must report a database name ending in `_test`
  before `TRUNCATE` runs.

## Release procedure

### 1. Prepare the release locally

Start from the project directory:

```bash
cd ~/devops-phase1/Phase1_Rerun/project2
source venv/bin/activate
git status -sb
git fetch origin
```

Review every local modification before continuing. Unrelated deleted or
untracked files must not be staged accidentally.

Validate Python, tests, migration topology, and model/schema agreement:

```bash
python -m compileall -q app config
python -m pytest -v
flask db heads
flask db history
FLASK_ENV=testing flask db current
FLASK_ENV=testing flask db check
git diff --check
```

Expected Week 8 results:

- 15 tests pass;
- exactly one Alembic head exists: `9f3b1c7a2d4e`;
- the test database is at that head;
- `flask db check` reports no pending model/schema operations.

### 2. Prove migrations can rebuild an empty database

The following commands destroy all data in the configured test database. The
guards must identify it as a `_test` database before this drill is attempted.

```bash
FLASK_ENV=testing flask db downgrade base
FLASK_ENV=testing flask db current
FLASK_ENV=testing flask db upgrade head
FLASK_ENV=testing flask db current
python -m pytest -v
```

Expected result: the empty test database upgrades through all three revisions,
ends at `9f3b1c7a2d4e`, and the complete suite still passes.

### 3. Identify production before backing it up

Link the CLI to the `accurate-mercy` project and `production` environment, then
verify the selected resources:

```bash
railway status
railway run --service Postgres --no-local bash -c \
  'psql "$DATABASE_PUBLIC_URL" -X -c "
    SELECT current_database(),
           pg_size_pretty(pg_database_size(current_database()));
    SELECT version_num FROM alembic_version;
  "'
```

Expected pre-Week-8-timezone state was database `railway` at revision
`731c6bd75249`. Stop if the project, environment, database, or revision is not
the expected target.

### 4. Take and inspect a production backup

Use a `pg_dump` client whose major version is the same as or newer than the
server. Railway was PostgreSQL 18.4 during this release, so PostgreSQL 18.6
client tools were used. PostgreSQL intentionally refuses a dump when the server
is newer than the client major version.

```bash
/usr/lib/postgresql/18/bin/pg_dump --version
mkdir -p /home/jay/railway-backups

railway run --service Postgres --no-local bash -c \
  '/usr/lib/postgresql/18/bin/pg_dump \
    --dbname="$DATABASE_PUBLIC_URL" \
    --format=custom \
    --compress=9 \
    --no-owner \
    --no-acl \
    --file=/home/jay/railway-backups/finance_tracker_before_timezone_2026-08-13.dump'

chmod 600 /home/jay/railway-backups/finance_tracker_before_timezone_2026-08-13.dump
sha256sum /home/jay/railway-backups/finance_tracker_before_timezone_2026-08-13.dump \
  > /home/jay/railway-backups/finance_tracker_before_timezone_2026-08-13.dump.sha256
sha256sum --check \
  /home/jay/railway-backups/finance_tracker_before_timezone_2026-08-13.dump.sha256

/usr/lib/postgresql/18/bin/pg_restore \
  --list /home/jay/railway-backups/finance_tracker_before_timezone_2026-08-13.dump \
  | sed -n '1,20p'
```

Recorded evidence for this release:

- custom-format gzip archive, mode `0600`;
- size 39 KiB and 94 table-of-contents entries;
- dumped by PostgreSQL 18.6 from PostgreSQL 18.4;
- SHA-256 integrity check returned `OK`;
- archive table of contents was readable by `pg_restore`.

This proves that the archive is present and structurally readable. It does
**not** prove complete recoverability. A full restore into an isolated
PostgreSQL 18 database is still required before this backup process can be
called restore-tested. Never test a restore by overwriting production.

### 5. Configure migration execution

On the Railway **application service** (`devops-phase1`), set the pre-deploy
command to:

```text
flask db upgrade
```

Railway executes this after the image is built and before the new application
starts, inside the private network with the service's environment variables. A
non-zero exit prevents that deployment from proceeding. The command must not be
configured on the PostgreSQL service.

### 6. Deploy through `main`

Merge the reviewed feature branch into `main` and push `main`. Railway watches
`main`; pushing only `week8-orm-refactor` does not update production.

Before merging, record the commits included in the release:

```bash
git log --oneline origin/main..origin/week8-orm-refactor
git diff --stat origin/main...origin/week8-orm-refactor
```

Watch both build and deploy logs. The required sequence is:

1. image builds successfully;
2. `flask db upgrade` exits successfully;
3. Gunicorn starts;
4. all workers boot;
5. Auth and Telegram blueprints register;
6. the health endpoint responds successfully.

### 7. Verify production after deployment

Check Alembic state using the public database connection exposed to the local
Railway command:

```bash
railway run --service Postgres --no-local bash -c \
  'psql "$DATABASE_PUBLIC_URL" -X -c \
    "SELECT version_num FROM alembic_version;"'
```

Expected result:

```text
9f3b1c7a2d4e
```

Verify all migrated timestamp columns:

```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE (table_name, column_name) IN (
  ('users', 'created_at'),
  ('users', 'updated_at'),
  ('users', 'last_login'),
  ('categories', 'created_at'),
  ('telegram_link_tokens', 'expires_at'),
  ('telegram_link_tokens', 'created_at'),
  ('telegram_user_preferences', 'updated_at'),
  ('transactions', 'created_at'),
  ('transactions', 'updated_at'),
  ('transactions', 'deleted_at'),
  ('budgets', 'last_used_at'),
  ('budgets', 'created_at'),
  ('budgets', 'updated_at'),
  ('budget_items', 'created_at'),
  ('budget_items', 'updated_at')
)
ORDER BY table_name, column_name;
```

All 15 rows must report `timestamp with time zone`.

### 8. Run production smoke tests

Use one controlled test account and uniquely labelled records. Do not modify a
real user's data.

- Log in and load the dashboard.
- List transactions and budgets.
- Create, read, update, refresh, and soft-delete a small transaction.
- Query that transaction directly and confirm its final amount and non-null
  `deleted_at`.
- Create a small budget with one item, toggle the item, rename the budget,
  refresh it, and delete it.
- Read Telegram status and preferences.
- Run `/balance`, add one clearly labelled Telegram transaction, confirm the
  balance changes, and remove the controlled record through the web app.
- Check application logs for HTTP 500 responses, tracebacks, failed workers, or
  repeated database errors.

The Week 8 release passed all of these checks.

## Rollback procedure

Rollback is a decision, not a reflex. First identify which layer failed.

| Failure | First response |
| --- | --- |
| New app fails before migration | Fix or redeploy the application; schema is unchanged |
| Migration command fails | Deployment should stop; inspect the Alembic/PostgreSQL error before retrying |
| Migration succeeds but app fails | Stop writes or enter maintenance mode, then assess code/schema compatibility |
| Data is corrupted or missing | Stop writes, preserve evidence, and prepare an isolated restore; do not repeatedly migrate |

For a schema rollback from `9f3b1c7a2d4e`:

1. announce maintenance and stop application writes;
2. take another backup of the current state;
3. confirm `SELECT version_num FROM alembic_version` returns
   `9f3b1c7a2d4e`;
4. deploy application code that is compatible with revision `731c6bd75249`;
5. run exactly `flask db downgrade 731c6bd75249` against production;
6. verify the revision, column types, application logs, and smoke tests;
7. reopen writes only after verification succeeds.

Do not downgrade to `base` in production. Do not restore the pre-release backup
merely to undo a migration: doing so would discard every valid write made after
the backup. Restore is the disaster-recovery path when forward repair and the
tested Alembic downgrade are unsuitable.

## Restore drill still required

The production dump has not yet been fully restored because the local server is
PostgreSQL 16 and the dump came from PostgreSQL 18. A valid drill requires an
isolated PostgreSQL 18 server and an empty disposable database. The drill must:

1. create the empty target from `template0`;
2. run `pg_restore` without `--clean` against that disposable target;
3. fail on any restore error;
4. verify Alembic revision, table counts, foreign keys, representative reads,
   and application startup;
5. delete only the disposable target after the evidence is recorded.

## References

- [Railway pre-deploy commands](https://docs.railway.com/deployments/pre-deploy-command)
- [Railway deployments](https://docs.railway.com/deployments)
- [PostgreSQL 18 `pg_dump`](https://www.postgresql.org/docs/18/app-pgdump.html)
- [PostgreSQL backup and restore](https://www.postgresql.org/docs/18/backup.html)
- [PostgreSQL 18 `pg_restore`](https://www.postgresql.org/docs/18/app-pgrestore.html)
- [Alembic command reference](https://alembic.sqlalchemy.org/en/latest/api/commands.html)

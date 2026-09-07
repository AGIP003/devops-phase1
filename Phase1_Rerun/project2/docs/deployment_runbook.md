# Moneytiq Deployment and Recovery Runbook

Last validated: 2026-09-07

## Production

- Backend: https://finance-tracker03.up.railway.app
- Deployment branch: `main`
- Platform: Railway
- Container source: `Phase1_Rerun/project2/Dockerfile`
- Health endpoint: `/health`
- Pre-deploy command: `flask db upgrade`
- Validated release: `d8b5d8e41b1f71cebd66448ad060c50ad92eb368`

## Deployment flow

1. Create a feature branch from `origin/main`.
2. Commit only the intended files.
3. Open a pull request into `main`.
4. GitHub Actions runs PostgreSQL tests, migrations, coverage and Docker checks.
5. Merge only when all required checks pass.
6. Railway waits for the `main` CI workflow.
7. Railway builds the Dockerfile.
8. Railway runs the pre-deploy migration.
9. Railway requests `/health`.
10. Railway activates the release after receiving a successful response.

## CI gates

The `test` job:

- Starts PostgreSQL 18.
- Applies Alembic migrations.
- Runs critical tests.
- Runs the full test suite.
- Enforces at least 70% coverage.
- Uploads test evidence.

The `docker` job:

- Depends on the test job.
- Builds the application image.
- Compiles packaged Python modules.
- Starts the image with Gunicorn.
- Calls `/health`.
- Verifies the container reports the expected Git SHA.

If the test job fails, the Docker job is skipped.

## Production verification

```bash
production_url="https://finance-tracker03.up.railway.app"

main_sha="$(
  git ls-remote origin refs/heads/main |
  awk '{print $1}'
)"

production_sha="$(
  curl --fail --silent --show-error \
    "$production_url/health" |
  python -c 'import json, sys; print(json.load(sys.stdin)["release"])'
)"

test "$main_sha" = "$production_sha"
```

## 1. CI failure response

1. Do not merge the pull request.
2. Open the failed GitHub Actions job.
3. Identify the first meaningful failure.
4. Reproduce it locally.
5. Fix the problem on the feature branch.
6. Push the correction.
7. Wait for all checks to pass.

Never bypass a required check merely to deploy faster.

## 2. Deployment health-check failure

1. Production remains on the previous healthy deployment.
2. Inspect Railway build, pre-deploy and application logs.
3. Confirm Gunicorn listens on Railway's `PORT`.
4. Confirm `/health` returns HTTP 2xx.
5. Check required environment variables.
6. Fix the problem through a new pull request.

## 3. Migration failure

1. Railway must not activate the new application release.
2. Inspect the Alembic error.
3. Do not manually mark a migration as applied.
4. Correct the migration and test it against a disposable database.
5. Submit the correction through CI.

Production migrations should be backward-compatible whenever possible.

## 4. Application rollback

1. Open the Railway service's deployment history.
2. Locate the last known-good deployment.
3. Confirm its Git SHA.
4. Select Railway's rollback action.
5. Wait for the health check.
6. Verify `/health` reports the expected SHA.
7. Run a non-destructive application smoke test.
8. Record the incident and reason for rollback.

Application rollback does not reverse database migrations.

## 5. Database recovery

The production PostgreSQL backup must be:

1. Created with PostgreSQL 18 tooling.
2. Stored in custom archive format.
3. Protected with restrictive permissions.
4. Accompanied by a SHA-256 checksum.
5. Restored into an isolated PostgreSQL 18 database.
6. Verified through schema, constraints, indexes, migration revision and row
   counts.
7. Tested through the Moneytiq SQLAlchemy application layer.

Never test restoration against the production database.

## 6. Secrets and sensitive data

1. Never commit `.env` files or database dumps.
2. Never print production connection strings.
3. Treat restored databases as production-sensitive data.
4. Keep backup files owner-readable only.
5. Store an encrypted copy off the development machine.

## 7. Current limitations

1. The manual backup is currently stored locally.
2. Automated encrypted off-device backups remain a production-hardening task.
3. Railway's deployment health check does not provide continuous monitoring.

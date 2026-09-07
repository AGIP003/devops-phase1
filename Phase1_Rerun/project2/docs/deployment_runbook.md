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

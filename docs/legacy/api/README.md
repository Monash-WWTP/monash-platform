# Monash WWTP platform API

This local FastAPI repository is the first foundation for a shared service for
CitizenFlood and the WWTP dashboard. Neither production client points to this
service yet. The simulation package was extracted from
`Monash-WWTP/wwtp-dashboard` commit `202b72e`; it is illustrative and
unvalidated, and its output must not be used as an operational or legal
compliance decision.

## Local development

Install `uv` and Docker, then run from the repository root:

```bash
docker compose -f compose.test.yaml up -d --wait db
export DATABASE_URL='postgresql+psycopg://monash_test:monash_test@127.0.0.1:5433/monash_test'
export TEST_DATABASE_URL="$DATABASE_URL"
export APP_ENV=development
uv sync --locked
uv run --locked alembic -c backend/alembic.ini upgrade head
uv run --locked python -m app.devdata
uv run --locked uvicorn app.main:app --reload
```

The explicit `devdata` command creates one synthetic `DEMO001` plant. It is
idempotent and refuses `APP_ENV=production`. The API does not create tables or
load remote data on startup. Alembic owns the application schema. The local
test service binds PostgreSQL only to `127.0.0.1:5433`; use a different
database and credentials for deployment.

The API documentation is at `http://127.0.0.1:8000/docs`; its machine-readable
contract is at `http://127.0.0.1:8000/openapi.json`. Health is
`GET /api/v1/health`.

## Verification

With the test database running and `DATABASE_URL`, `TEST_DATABASE_URL`, and
`APP_ENV=test` set:

```bash
uv run --locked alembic -c backend/alembic.ini upgrade head
uv run --locked alembic -c backend/alembic.ini check
uv run --locked python -m pytest -q backend/tests simulation/wwtp_sim/tests
uv run --locked python scripts/export_openapi.py
git diff --exit-code -- backend/openapi.json
```

Tests require the exact disposable URL shown above and require
`DATABASE_URL` to equal `TEST_DATABASE_URL`. The startup test reverses and
reapplies the migration, so do not use a database containing valuable data.

Scenario operations temporarily use the extracted Supabase Auth operator
adapter. The next identity work package replaces it with verified accounts
and server-side authorization. Current `SUPABASE_URL`, `SUPABASE_KEY`, and
`WWTP_OPERATOR_EMAILS` settings apply only to that temporary adapter.

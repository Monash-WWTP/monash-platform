# Local development and verification

Run from the repository root. PostgreSQL is disposable and bound to loopback port 5433. Do not change the test URL to a valuable database: tests reverse and reapply the schema.

```sh
docker compose -f infra/local/compose.test.yaml up -d --wait db
export DATABASE_URL='postgresql+psycopg://monash_test:monash_test@127.0.0.1:5433/monash_test'
export TEST_DATABASE_URL="$DATABASE_URL"
export APP_ENV=test
uv sync --locked
uv run --locked alembic -c services/api/alembic.ini upgrade head
uv run --locked alembic -c services/api/alembic.ini check
uv run --locked pytest -q services/api/tests packages/simulation/wwtp_sim/tests tests
uv run --locked python scripts/export_openapi.py
git diff --exit-code -- services/api/openapi.json
uv run --locked python scripts/check_import_inventory.py --verify-targets
uv run --locked python scripts/check_repository.py
```

For a synthetic API demo, set `APP_ENV=development`, run `uv run --locked python -m app.devdata`, then `uv run --locked uvicorn app.main:app --reload --host 127.0.0.1`. The seed is idempotent and rejects production. Confirm health with `curl --fail http://127.0.0.1:8000/api/v1/health`.

API environment: `DATABASE_URL` is required; `APP_ENV`, `CORS_ORIGINS`, `SUPABASE_URL`, `SUPABASE_KEY` and `WWTP_OPERATOR_EMAILS` configure the temporary integration. Do not open operator access by weakening the dependency. The empty default allowlist denies mutations.

[Dashboard](../../apps/dashboard/README.md) and [mobile](../../apps/citizenflood/README.md) commands are independent. Both retain legacy integration. API tests mock authentication and use synthetic data; they do not call production services. [Research reproduction](../../research/README.md) is optional and separately installed.

Stop the database with `docker compose -f infra/local/compose.test.yaml down`. This retains its named volume. Deleting the volume is a separate destructive reset; it is never part of onboarding.

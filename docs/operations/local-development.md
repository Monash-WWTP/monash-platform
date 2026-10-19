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

For a synthetic API demo, set `APP_ENV=development`, run `uv run --locked python -m app.devdata`, then `uv run --locked uvicorn app.main:app --reload --host 127.0.0.1 --port 8181`. The seed is idempotent and rejects production. Confirm health with `curl --fail http://127.0.0.1:8181/api/v1/health`.

API environment: `DATABASE_URL` is required. Current authentication uses OIDC issuer/discovery/JWKS, browser client secret/callback/web origin, issuer-subject account mapping, server-owned capabilities and operator MFA. Private photos require the configured S3 endpoint/bucket/access credentials. See `services/api/app/config.py` and `infra/staging/.env.example`; never copy real secrets into Git or chat. Legacy Supabase configuration remains for ownership-claim compatibility, not general operator authorization.

`/api/v1/health` is process liveness. `/api/v1/ready` checks the migrated database and, when configured, private bucket access and identity signing-key availability. Production settings require those integrations. Database connection acquisition and statements, storage and identity probes use bounded waits; a healthy database alone no longer establishes integrated readiness. Readiness needs bucket head permission. These probes do not replace login/upload acceptance.

[Dashboard](../../apps/dashboard/README.md) and [mobile](../../apps/citizenflood/README.md) source clients use the versioned API. The published APK remains legacy. API tests use synthetic identities/data and a disposable database; storage tests use an in-memory double, so they do not prove a deployed S3 service. [Research reproduction](../../research/README.md) is optional and separately installed.

Stop the database with `docker compose -f infra/local/compose.test.yaml down`. This retains its named volume. Deleting the volume is a separate destructive reset; it is never part of onboarding.

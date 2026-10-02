# Monash platform

Successor monorepo for CitizenFlood, the WWTP operator dashboard, and a shared FastAPI service. The three products build and release independently.

| Product | Purpose | Current integration |
| --- | --- | --- |
| [CitizenFlood](apps/citizenflood/README.md) | Mobile citizen observations and reporting | Imported Supabase flows |
| [WWTP dashboard](apps/dashboard/README.md) | Lab monitoring and illustrative scenarios | Imported Supabase reads and legacy `/api/*` service |
| [Platform API](docs/api/README.md) | API-owned PostgreSQL, scenarios and simulation | Local `/api/v1`; clients are not cut over yet |

Authentik accounts, reporting/monitoring endpoints, client cutover and server deployment are the next [work packages](docs/migration/ROADMAP.md). The simulation is `illustrative_unvalidated`; see [scientific limits](docs/science/VALIDATION.md).

## First-day setup

Use Python 3.12+, uv, Docker with Compose, Node 22/npm, and Flutter 3.44.7 with an Android SDK and JDK 17. [Toolchain evidence](docs/operations/toolchains.md) records local versions. Commands start at the repo root.

API and disposable database:

```sh
docker compose -f infra/local/compose.test.yaml up -d --wait db
export DATABASE_URL='postgresql+psycopg://monash_test:monash_test@127.0.0.1:5433/monash_test'
export TEST_DATABASE_URL="$DATABASE_URL"
export APP_ENV=development
uv sync --locked
uv run --locked alembic -c services/api/alembic.ini upgrade head
uv run --locked python -m app.devdata
uv run --locked uvicorn app.main:app --reload --host 127.0.0.1
```

Swagger: <http://127.0.0.1:8000/docs>; schema: <http://127.0.0.1:8000/openapi.json>. The seed is synthetic and idempotent. Tests reset the disposable schema. See [local development](docs/operations/local-development.md).

Dashboard, in another terminal:

```sh
npm --prefix apps/dashboard ci
npm --prefix apps/dashboard run lint
npm --prefix apps/dashboard run build
npm --prefix apps/dashboard run dev
```

Monitoring still uses legacy Supabase. Scenario calls need a compatible legacy API supplied with `VITE_API_BASE`; the successor service does not serve old `/api/*` paths.

Mobile:

```sh
cd apps/citizenflood
flutter pub get
flutter analyze
flutter test
flutter build apk --debug --dart-define=SUPABASE_URL=https://example.supabase.co --dart-define=SUPABASE_ANON_KEY=synthetic-ci-key
```

Synthetic values produce a verification artifact. Configure an approved development project as described in the app README for an operational run.

## Engineering and research

- [Architecture](docs/architecture/README.md)
- [Source origins, hashes and restricted material](docs/migration/SOURCE_ORIGINS.md)
- [Research reproduction](research/README.md) and [licensed snapshot](data/public/README.md)
- [Server prerequisites, backup and restore gate](docs/operations/deployment.md)
- [Contribution and checks](CONTRIBUTING.md)

Historical docs, Supabase migrations and helpers under `docs/legacy/` and `legacy/` are inactive references. `services/api/alembic` is the only active application migration chain. No software license is inferred from the data license; software publication needs an owner decision.

The [approved repository design](docs/superpowers/specs/2026-10-02-unified-platform-repository-design.md) and [implementation plan](docs/superpowers/plans/2026-10-02-unified-platform-repository.md) are retained as planning records; use the migration roadmap for current delivery status.

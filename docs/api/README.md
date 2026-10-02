# Platform API contract

Swagger is at <http://127.0.0.1:8000/docs>; the live schema is at <http://127.0.0.1:8000/openapi.json>. The tracked [OpenAPI snapshot](../../services/api/openapi.json) defines implemented shapes. Generate it with `uv run --locked python scripts/export_openapi.py`; CI checks drift.

Current `/api/v1` endpoints cover health, plants, scenarios, models, scenario runs, run results/time series and comparisons. Reporting, monitoring and accounts are planned. Health does not query the database. Startup creates no tables and fetches no remote data: apply Alembic explicitly.

Scenario mutations and execution require a bearer session validated by the temporary Supabase operator adapter. Its email must be confirmed and in `WWTP_OPERATOR_EMAILS`; an empty allowlist fails closed. Auth service failure returns an unavailable error. Read permissions are defined by the actual handlers/snapshot, not hidden UI controls. The identity work package replaces this adapter.

Errors use an envelope, with `X-Request-ID` for correlation:

```json
{"error":{"code":"plant_not_found","message":"Plant not found","request_id":"...","details":null}}
```

Validation errors are HTTP 422 with field/message details. Unexpected errors hide exception text. Current list endpoints do not implement pagination; add pagination/filtering with the monitoring contract before exposing larger datasets.

Concentrations use mg/L, flow/capacity MLD, availability percent and dates ISO format. Carbon outputs are assumed scenario intensities in kg CO2-eq/m³, not measured plant emissions. See [scientific limits](../science/VALIDATION.md).

Change schemas, handlers, contract tests and snapshot together. Generated TypeScript/Dart clients and stale-contract checks are a later cutover gate. Client builds alone do not prove API compatibility.

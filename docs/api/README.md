# Platform API contract

The tracked [OpenAPI snapshot](../../services/api/openapi.json) defines implemented request and response shapes. Generate it with `uv run --locked python scripts/export_openapi.py`; CI checks drift. Local staging serves Swagger at <http://127.0.0.1:8181/docs> and the live schema at <http://127.0.0.1:8181/openapi.json>. Production proxy configuration keeps those unversioned routes private.

`/api/v1` covers plants, scenarios, immutable simulation runs, replay and comparison, laboratory monitoring, legacy citizen reports and private media, moderation, operator response, account sessions/settings, administration, identity events and migration claims. `/api/v2` covers the current observation protocol, references, submission/history, moderation and privacy-filtered community observations. Both versions must pass through the deployment proxy. V1 reporting remains a compatibility contract; the current mobile reporting flow uses v2.

`/api/v1/health` is process liveness. `/api/v1/ready` checks configured dependencies. Neither a passing build nor liveness proves production readiness. Startup creates no tables: apply Alembic explicitly.

Authentication uses OIDC with a shared issuer. Browser login uses a backend-held session and secure, HTTP-only cookie; mutations require CSRF protection. Mobile uses authorization code with PKCE and bearer tokens. Server dependencies enforce verified citizenship, capabilities and MFA for privileged actions; hiding a UI control does not authorize a request. Account settings links remain disabled unless their identity flows are provisioned and `ACCOUNT_SETTINGS_ENABLED=true`.

Errors use an envelope and `X-Request-ID` for correlation, including requests rejected by the body-size limit:

```json
{"error":{"code":"plant_not_found","message":"Plant not found","request_id":"...","details":null}}
```

Validation errors are HTTP 422 with field/message details. Unexpected errors hide exception text. Monitoring, reporting and administrative list handlers provide endpoint-specific pagination; consult their schema rather than assuming every list has the same shape. Upload requests are bounded at 11 MiB; accepted image files have a separate 10 MiB limit and image validation. Private photos require authorization and are not exposed in public community projections.

Concentrations use mg/L, flow/capacity MLD, availability percent and dates ISO format. Carbon outputs are assumed scenario intensities in kg CO2-eq/m³, not measured plant emissions. See [scientific limits](../science/VALIDATION.md).

Change schemas, handlers, contract tests and snapshot together. Client builds alone do not prove API compatibility; release acceptance must exercise the real identity, proxy and storage configuration.

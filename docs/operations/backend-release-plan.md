# Shared backend release plan

Assessment date: 2026-10-03. Status: release proposal; production cutover is not ready. Hosting location remains an owner input. This document operationalizes the existing shared-platform design and migration roadmap; it does not claim missing features are implemented.

## Current evidence

- Fresh local verification: 65 Python tests pass against isolated test PostgreSQL; these tests establish the implemented foundation, not production readiness.
- FastAPI exposes `/api/v1` plants, scenarios, runs, model metadata, comparison and health, with a checked OpenAPI snapshot, structured errors, request IDs and Alembic migrations.
- Startup does not create schemas or seed data. The explicit development fixture rejects `APP_ENV=production`; it must never run against production.
- Current authorization still validates Supabase sessions and an operator email allowlist. authentik, verified shared registration, application roles and browser sessions are not implemented.
- Citizen reports/media/moderation and monitoring stations/lab samples are not implemented in the new API. Both clients retain direct Supabase paths.
- Dashboard simulation requests use `/api/*`; the new backend only exposes `/api/v1/*`. Its Vercel proxy still targets the legacy Render API. Changing only the hostname is insufficient.
- Infrastructure currently provides test PostgreSQL only. There is no checked production container/Compose stack, identity setup, TLS routing, readiness dependency check, off-server backup/restore or deployment pipeline.
- Simulation runs still depend on mutable scenarios and can be cascade-deleted. Immutable snapshots, full provenance and durable failure states remain release work. Models remain illustrative and unvalidated.

## Target and deployment choice

Keep the website on Vercel. Host FastAPI separately on a Linux server using Docker Compose initially, with a TLS reverse proxy, application PostgreSQL, authentik and its separate identity database, and private S3-compatible photo storage. Application PostgreSQL is a separate database service under backend ownership, not embedded inside the API container. Only HTTPS is public; database ports remain private. Containers use pinned versions/digests, least-privilege credentials and persistent volumes. Production data, passwords, signing keys and local environment files never enter Git.

Recommended order: isolated staging first; production on the standalone server when release gates pass. Reuse the same image and infrastructure definition between environments. Start with one API deployment; measure traffic and simulation duration before choosing worker counts/server size. Add a separate simulation worker when measured runtime requires it, with persisted job states before accepting asynchronous jobs. Kubernetes is not required for the initial release.

Alternative: managed API/PostgreSQL/storage initially reduces operations work, but identity, client migration and restore verification are still required. A server already available can run staging in isolation, provided production/test credentials, databases and storage do not overlap.

Use owner-controlled stable domain names before compiling the next APK. Example names below are illustrative addresses, not existing deployments:

- `https://water.<owned-domain>`: Vercel website/dashboard.
- `https://api.<owned-domain>/api/v1`: FastAPI contract.
- `https://accounts.<owned-domain>`: authentik OIDC issuer.

A same-origin `/api/v1/*` and `/auth/*` proxy from the website to the backend preserves the design's HTTP-only browser session. Proxy callback, Set-Cookie, CSRF, forwarded headers and cache behavior must be integration-tested on Vercel; use a backend web-origin reverse proxy if those guarantees cannot be established. Private/authenticated responses must not be CDN-cached. Mobile calls the API hostname directly.

## Independently deliverable work packages

Each feature package needs a focused implementation plan from the existing architecture spec before coding; deployment configuration can be prepared before server access arrives.

1. **Staging runtime.** Create `services/api/Dockerfile`, `infra/server/compose.yaml`, reverse-proxy configuration and `.env.example`; add `/api/v1/ready` with bounded PostgreSQL/schema checks alongside liveness. Run migrations once as a release job. Prove reproducible build, missing-secret failure, DB-down readiness failure, restart/reboot and migration rollback/forward compatibility. No synthetic production seeds. A staging URL and OpenAPI docs are the deliverable; clients remain on current production endpoints.
2. **Shared identity.** Configure authentik and email delivery, verified citizen registration/recovery, invited operator MFA and application roles keyed by `(issuer, subject)`. Implement browser login/callback/logout with HTTP-only session and CSRF, and Android external-browser authorization code with PKCE; Android contains no client secret. Test issuer/audience/signature/expiry, citizen/operator separation, logout/recovery and provider outage. Do not infer old anonymous ownership from email. This replaces the transitional Supabase operator allowlist.
3. **Monitoring and migration rehearsal.** Add stations/samples/approved community read contracts with pagination/filtering, source provenance and privacy projection. Rehearse a permission-controlled real-data migration with counts, IDs, units, timestamps, status and media hashes reconciled. Missing values stay missing; citizen observations never become lab readings. Restrict access to any staging copy of real personal data.
4. **Citizen writes, photos and moderation.** Add owner reports/history, idempotent submissions, scoped photo upload/download, bounded file validation, moderation and audit history. Test duplicate retries, cross-owner reads, rejected/approved projection, precise-coordinate privacy, storage failure and partial uploads. Verified registration is required for the new client. Old anonymous ownership links require proof of the old authenticated subject and the new account.
5. **Simulation evidence.** Persist input/plant/limits/factor/model/artifact/time snapshots and explicit failure states. Preserve runs when scenarios change or are removed; replay generates a new record. Test scenario edit/delete independence, reproducibility, invalid inputs and failure without invented output. Scientific validation remains a separate gate: do not present heuristic results as measured or decision-approved outputs.
6. **Client integration.** Generate/check TypeScript and Dart contracts from `services/api/openapi.json`. Change dashboard `src/api/client.ts`, monitoring/auth modules and Vercel routing to `/api/v1`; update CitizenFlood config, auth, report repository and media flows to the API. Test shared login, citizen submission/history, operator moderation, approved public output and dashboard monitoring on staging. Build a new APK using the existing signing identity and increased versionCode; the published APK cannot be redirected by a website change.
7. **Production release and recovery.** Verify encrypted off-server backups of app DB, identity DB/configuration and photos through an actual restore; define agreed recovery objectives and measured load acceptance. Set up structured logs, redaction, error/latency/storage alerts, rate limits and release image digests. Rehearse write freeze, final export/import, reconciliation, endpoint/client switch and rollback. Account for new writes when rolling back: retain/export them; do not blindly restore an old snapshot. Remove direct legacy writes only after the acceptance window closes and supported old-client behavior is communicated. Preserve legacy repos and rollback records.

## Connection contract

The browser and APK never receive PostgreSQL credentials. FastAPI owns SQL and photo access rules. The dashboard uses same-origin session-protected API calls; mobile presents short-lived OIDC access tokens, stores refresh credentials in platform secure storage and uses the same account issuer. Roles remain distinct even when one person uses both products.

Server settings include `APP_ENV=production`, private `DATABASE_URL`, explicit allowed browser origins, identity issuer/audience/session secrets, storage endpoint/bucket/credentials and mail delivery configuration as each module is implemented. The current code does not recognize all future settings yet. Do not configure imaginary variables and assume functionality exists.

Swagger UI at `/docs` and the OpenAPI contract document methods, request bodies and responses. Add realistic descriptions and authorization requirements as modules arrive. Decide public versus authenticated docs access at release; documentation exposure never bypasses endpoint authorization.

## Go/no-go checklist

- [ ] Production infrastructure and domain ownership/access confirmed.
- [ ] Shared identity, capability/ownership/privacy tests and recovery pass.
- [ ] Real migration reconciles without fabricated values.
- [ ] Report/media/moderation/monitoring and immutable run paths pass.
- [ ] Both client contracts and real-device Android login/update pass.
- [ ] Dependency readiness, logging, load and off-server restore pass.
- [ ] Cutover and rollback rehearsal includes preservation of new writes.
- [ ] Owners review scientific limitations and operational release evidence.

Current answer: foundation can be prepared for staging; it is not the full shared production backend. Keep the live APK and dashboard on their current data paths until these gates pass.

References: [existing architecture](../superpowers/specs/2026-10-02-shared-platform-architecture-design.md), [migration roadmap](../migration/ROADMAP.md), [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/), [authentik OIDC provider](https://docs.goauthentik.io/add-secure-apps/providers/oauth2/).

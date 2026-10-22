# Production preparation

These templates are reviewable preparation for a future server. No production server has been provisioned and this stack has not been deployed or qualified. The dashboard stays on its existing Vercel hosting. Caddy exposes only the API and identity hosts; it does not build or serve the dashboard.

Read the [server setup guide](../../docs/operations/production-server-setup.md) and the [current acceptance record](../../docs/operations/staging-acceptance-2026-10-18.md) before execution. The instructions below describe future operator steps, not evidence of completion.

## Required decisions and inputs

Assign the server/hosting and recovery owners, approved API and identity domains, DNS, resource budget, backup destination and RPO/RTO. Confirm the host is supported for Docker Engine/Compose and public ports 80/443. No database, API-internal or identity-internal port is published by Compose. Enforce the host firewall as well.

Copy `.env.example` to a private `.env`, restrict its permissions and fill every value. Blank/missing inputs fail Compose interpolation. Use `API_IMAGE` and `CADDY_IMAGE` with reviewed immutable image digests; retain the prior API image for rollback. Postgres 16.13 and authentik 2026.8.3 match the existing staging version pins; review their security/support status and resolved digests before deployment. Version pins and synthetic rendering tests are not image qualification.

Use distinct, random secrets; `APP_DB_PASSWORD` must be URL-safe because it is interpolated into the database URL. The database user currently owns its application database for migrations. Separate migration/runtime roles and tested grants remain a production acceptance task; this template does not silently create an untested permissions model. Environment variables are visible to authorized Docker administrators; protect host access and avoid recording rendered configuration containing secrets.

Configure an existing **private HTTPS S3-compatible bucket** and its actual region, with scoped head/read/write/delete permissions and independent recovery. This stack provisions no object store. Verify anonymous reads are denied. Configure an external authenticated STARTTLS mail service; this template assumes its TLS mode and must be reviewed if the provider requires implicit TLS instead.

`WEB_ORIGIN` is the existing HTTPS Vercel dashboard origin without a trailing slash. `OIDC_CALLBACK_URL` must be the exact dashboard-origin `/api/v1/auth/callback` URL through its same-origin proxy. Before client cutover, configure that proxy to the new API host, preserve cookie/Origin/CSRF behavior, and verify the callback, logout and authenticated requests end to end. Merely allowing CORS does not provide a credentialed cross-origin session flow.

Set `OIDC_ISSUER`, `OIDC_DISCOVERY_URL` and `OIDC_JWKS_URL` to the exact reviewed public provider metadata values. All three clients require the shared issuer and signing keys; distinct `OIDC_MOBILE_ISSUER` values are unsupported and rejected by application configuration. The API uses public identity endpoints, so verify DNS/TLS reachability from inside its container. No unreviewed internal identity backchannel is enabled.

## Identity provisioning

Provision authentik through a reviewed administrative procedure after initial installation; create and secure the initial administrator using authentik's supported setup flow. This template deliberately supplies no default administrator password/token and mounts no Docker socket. Review enrollment, verified-email mapping, email recovery, issuer/UUID subject mapping and exact redirect URIs against [the server guide](../../docs/operations/production-server-setup.md).

Keep `ACCOUNT_SETTINGS_ENABLED=false` until the shared profile, email, password and session-security flows from the identity reference have been provisioned and tested, including security-event revocation. Set it true only after that acceptance.

Configure `monash-web` and `monash-operator` as confidential clients using the configured shared `OIDC_CLIENT_SECRET`, and `citizen-mobile` as public PKCE with the exact Android callback. Require MFA for the operator authentication flow. Review the existing [staging identity bootstrap](../staging/identity/bootstrap.py) as implementation reference only: it contains localhost URLs and is **not** a production provisioning script.

Install and test the reviewed recovery/disable event integration. Both identity processes receive the same `IDENTITY_EVENT_SECRET`, exact `MONASH_EVENT_ISSUER` and internal API event endpoint. Supplying these environment variables does not install policies or establish delivery. Password reset must invalidate existing browser sessions and bearer proofs; account disable must remove capabilities. Test failure behavior and delivery/reconciliation for identity administration events before acceptance.

## Future execution sequence

From this directory on the future provisioned server, with private `.env` populated:

```sh
# Validation only; --quiet avoids printing resolved secrets.
docker compose config --quiet
# Start TLS/identity independently; do not wait for API readiness here.
docker compose up -d database identity-db identity-server identity-worker caddy
# Validate Caddy configuration against the chosen image.
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
# After DNS/TLS, identity provisioning, SMTP and S3 acceptance:
docker compose up -d --wait api
```

The API has a mandatory successful migration dependency. Migration failure prevents API startup. Neither migration nor startup imports data or runs synthetic seeds. Caddy has no dependency on API readiness: it must serve the public identity host before the API can probe its signing keys. Starting Caddy while an upstream is absent may temporarily return 502 on that host; do not treat that phase as cutover acceptance.

Compose healthchecks probe readiness and all services use bounded local log rotation. Docker does not automatically restart a running process solely because it becomes unhealthy. Establish redacted alerts, rate/concurrency controls and measured capacity before accepting users; no request-rate policy or host sizing is invented here.

## Acceptance and rollback evidence still required

- From another network, verify public DNS/TLS and that only intended ports are reachable. Verify Caddy restricts API routing to `/api/v1` and `/api/v2` and the API container can reach public identity metadata.
- Verify registration, verified email, mail delivery/recovery, invited operator MFA, least-privilege capability assignment and reset/disable revocation through the real clients.
- Verify report retry/ownership, photo upload/download and denied anonymous storage access, moderation and public privacy projection; reconcile any authorized imports against source records.
- Verify Vercel same-origin proxy sessions/CSRF and the qualified mobile release independently. Retain legacy client endpoints until their authorized cutover.
- Measure expected read/upload/simulation concurrency, record failures/latency/resources and establish request/concurrency limits and redacted monitoring.
- Back up both databases, identity state, object storage and release/config custody to independent storage. Restore into an isolated environment and record RPO/RTO, counts, ownership and object hashes.
- Record release digests/schema/client revisions, acceptance owner and a rollback checkpoint. Retain prior images and legacy services; reconcile writes before rollback and never blindly restore an old database over newer user data.

Run `python -m pytest -q tests/test_production_config.py` from the repository root for synthetic Compose rendering and missing-input checks. Those tests start no services and prove neither network reachability nor production readiness.

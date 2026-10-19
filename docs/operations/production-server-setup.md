# Production server setup

Status: preparation guide, 2026-10-19. The successor API has **not been deployed** and no production API/account domain is assigned. The static Vercel site is live, but its inherited Render destination does not provide the dashboard's `/api/v1` contract. A successful frontend build does not resolve this P0 blocker.

This runbook uses the current API Dockerfile and settings. It is not a claim that a production Compose stack, identity provisioning or restore drill has been qualified. `infra/staging/compose.yaml`, `scripts/staging*.py` and `infra/staging/identity/bootstrap.py` are local staging tools with localhost URLs, test mail and local custody paths: **do not run them unchanged in production**.

## 1. Prepare the information and server

For the estimated initial audience of 20–50 people, a Linux server with 4 vCPU, 8 GB RAM and 80 GB SSD is a planning starting point, not a measured capacity guarantee. Run one API process initially; simulations, simultaneous uploads and accumulated photos determine actual needs. Prefer Ubuntu 24.04 LTS or another OS supported by the chosen Docker release.

Record these values before configuring the release:

| Value | Purpose |
| --- | --- |
| Server IP, SSH administrator and provider console access | Installation and emergency access |
| `api.<your-domain>` | Public server API; DNS A/AAAA points to the server |
| `accounts.<your-domain>` | Public authentik identity service on the server |
| Actual Vercel/custom website origin | Exact browser origin and callback; no trailing slash |
| SMTP host, port, TLS mode, username/password and verified sender | Real registration/recovery mail |
| Private S3 endpoint, bucket, region and restricted credentials | Photo storage; never a public bucket |
| Recovery owner and deputy | People who can restore databases, identity, photos, DNS and secrets |
| Agreed RPO and RTO | Maximum acceptable data loss and downtime; proposals require owner agreement |
| Expected peak users and daily photo count/size | Load and storage acceptance |

Illustrative URL values below use `example.com`; replace every occurrence. Keep the existing Vercel website until server acceptance passes. Do not switch the published Android APK by changing the website.

Create a non-root SSH administrator with key authentication. Test a second SSH session and provider console before disabling password/root SSH. Install Docker Engine and Compose from the [official Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/), and Caddy from its [official installation instructions](https://caddyserver.com/docs/install). Install Git, CA certificates and a supported PostgreSQL client for backup/administration.

Allow public TCP 80/443; restrict SSH to administrators/VPN where possible. Do not expose PostgreSQL, S3 administration, Docker sockets or internal API ports. Docker-published ports can bypass UFW rules; use private container networking or explicit loopback bindings as well as the provider firewall. See [Docker firewall behavior](https://docs.docker.com/engine/network/packet-filtering-firewalls/).

Create a restricted deployment directory outside any public web root, for example `/srv/monash`. Store environment files with mode `0600`, directories `0700`, and an encrypted off-server copy of recovery secrets. Do not paste credentials into tickets, Git, shell command arguments or this document.

## 2. Build an immutable API image

Check out an approved commit on the build machine; use a read-only deploy credential for the private repository. Build from the repository root:

```sh
git rev-parse HEAD
docker build -f services/api/Dockerfile -t monash-api:RELEASE_COMMIT .
docker image inspect monash-api:RELEASE_COMMIT --format '{{.Id}}'
```

Replace `RELEASE_COMMIT` with the approved SHA. Record the SHA, image ID/registry digest and dependency scan. Transfer that exact image to the server through a private registry or `docker save`/`docker load`; never deploy a mutable `latest` tag. The Dockerfile runs the API as UID 10001 and includes migration code. It does not include the repository's administrative/import scripts.

## 3. Install identity and private photo storage first

Run authentik server/worker with its own PostgreSQL database and durable data, independently from the application database. Start from the [official Compose installation](https://docs.goauthentik.io/install-config/install/docker-compose/) and review it against the release version. The staging repository pins authentik `2026.8.3`; qualify upgrades rather than mixing untested versions. Bind authentik HTTP to `127.0.0.1:9100`, disable public database bindings, and put HTTPS in front of it. Configure trusted proxy networks using the [authentik reverse-proxy guidance](https://docs.goauthentik.io/install-config/reverse-proxy/).

Use real TLS-enabled SMTP, a stable authentik secret key, a unique database password and an administrator with MFA. Remove temporary bootstrap tokens after installation. Do not use Mailpit or a `.localhost` sender in production.

Provision these application contracts in authentik, using `infra/staging/identity/bootstrap.py` as a **reviewed reference**, not an unmodified production command:

- `monash-web` and `monash-operator`: confidential clients; exact redirect `https://water.example.com/api/v1/auth/callback`. The current API has one `OIDC_CLIENT_SECRET`, so both confidential providers must use that configured secret unless the implementation changes.
- `citizen-mobile`: public client with PKCE, no embedded secret, exact callback `au.edu.monash.citizenflood:/oauthredirect`. The current published APK remains legacy; qualify the next build separately.
- Match the reference's global issuer and stable `user_uuid` subject, signing key, scope mappings, verified-email claim, operator MFA/AMR claim, registration and recovery flows. The API checks these claims; standard OAuth providers alone are insufficient.
- Configure real enrollment email verification and recovery. Replace all localhost redirects. Configure the credential-reset event hook with the same `IDENTITY_EVENT_SECRET` as the API, the exact issuer and a reachable `/api/v1/identity/events` endpoint. Verify that password recovery revokes existing application sessions.
- Determine issuer, discovery and JWKS URLs from the actual provider metadata. They must agree exactly; do not infer the issuer from an example hostname. If the mobile provider has a distinct issuer, set `OIDC_MOBILE_ISSUER` accordingly.

Store photos in a private S3-compatible bucket. Managed object storage is an option even when the API runs on this server. For on-server storage, provision a supported S3 service with persistent data and off-server backups; a single disk is not redundancy. Give the API only the bucket permissions required for head/list/read/write/delete operations. Keep storage credentials separate from backup/admin credentials. Test both allowed access and denial of anonymous reads. Set `STORAGE_REGION` to the service's real region; the source default `garage` is not universal.

## 4. Configure the application database and API

The following is a **minimal deployment example to review and save on the server**, not a committed or qualified production stack. Identity and S3 must already be reachable. Save it as `/srv/monash/compose.yaml`:

```yaml
name: monash-production
x-api: &api
  image: ${API_IMAGE:?set immutable API image}
  env_file: ./api.env
  restart: unless-stopped
services:
  database:
    image: postgres:16.13
    env_file: ./database.env
    volumes:
      - application_db:/var/lib/postgresql/data
    healthcheck:
      test: [CMD-SHELL, 'pg_isready -U monash -d monash']
      interval: 5s
      timeout: 3s
      retries: 20
    restart: unless-stopped
  migrate:
    <<: *api
    restart: 'no'
    profiles: [release]
    command: [uv, run, --no-sync, alembic, -c, services/api/alembic.ini, upgrade, head]
    depends_on:
      database: {condition: service_healthy}
  api:
    <<: *api
    ports: ['127.0.0.1:8181:8000']
    depends_on:
      database: {condition: service_healthy}
    healthcheck:
      test: [CMD, /workspace/.venv/bin/python, -c, "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/ready',timeout=10)"]
      interval: 30s
      timeout: 15s
      retries: 3
volumes:
  application_db:
```

Pin reviewed base/service image digests for the release; do not assume historical version pins are an ongoing security policy. Add Docker log rotation (for example `local` logging with bounded files) before accepting traffic. Docker health status alone does not restart an unhealthy but running process; alert on failed readiness.

Create a private Compose `.env` containing `API_IMAGE=monash-api:RELEASE_COMMIT`, and `database.env`:

```dotenv
POSTGRES_DB=monash
POSTGRES_USER=monash
POSTGRES_PASSWORD=REPLACE_WITH_RANDOM_URL_SAFE_SECRET
```

Create `api.env` using the actual settings names below. The database password must match; percent-encode it in the URL if it contains URL-reserved characters. Use a URL-safe random secret to simplify this. The example database user owns its database for initial migration; establish separate migration/runtime roles and verified grants before accepting production traffic.

```dotenv
APP_ENV=production
AUTH_MODE=oidc
DATABASE_URL=postgresql+psycopg://monash:REPLACE_WITH_RANDOM_URL_SAFE_SECRET@database:5432/monash
WEB_ORIGIN=https://water.example.com
CORS_ORIGINS=https://water.example.com
SESSION_SECURE=true
OIDC_ISSUER=https://accounts.example.com/
OIDC_DISCOVERY_URL=https://accounts.example.com/application/o/monash-web/.well-known/openid-configuration
OIDC_JWKS_URL=https://accounts.example.com/application/o/monash-web/jwks/
OIDC_CLIENT_ID=monash-web
OIDC_OPERATOR_CLIENT_ID=monash-operator
OIDC_MOBILE_CLIENT_ID=citizen-mobile
OIDC_CLIENT_SECRET=REPLACE_WITH_CONFIDENTIAL_CLIENT_SECRET
OIDC_CALLBACK_URL=https://water.example.com/api/v1/auth/callback
IDENTITY_EVENT_SECRET=REPLACE_WITH_SHARED_RESET_EVENT_SECRET
STORAGE_ENDPOINT=https://REPLACE_WITH_PRIVATE_S3_ENDPOINT
STORAGE_BUCKET=citizen-photos
STORAGE_REGION=REPLACE_WITH_ACTUAL_REGION
STORAGE_ACCESS_KEY=REPLACE_WITH_BUCKET_ACCESS_KEY
STORAGE_SECRET_KEY=REPLACE_WITH_BUCKET_SECRET
```

`OIDC_BACKCHANNEL_ORIGIN` is optional for a reviewed internal identity connection; leave unset when using the public HTTPS endpoints. If used, ensure it cannot change the expected issuer, and verify discovery/token/JWKS behavior. Do not disable secure sessions to get around a proxy problem.

From `/srv/monash`, start the database and explicitly migrate before starting the API:

```sh
docker compose up -d --wait database
docker compose --profile release run --rm migrate
docker compose up -d --wait api
curl --fail --max-time 20 http://127.0.0.1:8181/api/v1/health
curl --fail --max-time 20 http://127.0.0.1:8181/api/v1/ready
```

Stop if migration/readiness fails; inspect redacted logs, not the contents of environment files. Production startup does not create schemas or seed data. Never run `app.devdata` in production. Import approved monitoring/private data using the existing import tools from a secured administration environment with the correct release and destination settings; reconcile counts, station codes, missing/BDL values and source provenance before public acceptance. An empty array is a valid contract response, but it does not prove the intended dataset was imported.

## 5. Put HTTPS in front of the services

After DNS resolves correctly, use this host Caddyfile with the loopback bindings above:

```caddyfile
api.example.com {
    @versioned path /api/v1 /api/v1/*
    handle @versioned {
        header Cache-Control "no-store"
        reverse_proxy 127.0.0.1:8181
    }
    handle {
        respond "Not found" 404
    }
}
accounts.example.com {
    reverse_proxy 127.0.0.1:9100
}
```

Validate with `sudo caddy validate --config /etc/caddy/Caddyfile` before reloading the Caddy service. Keep port 80 available for certificate issuance/renewal as required by your ACME configuration. This configuration preserves the `/api/v1` prefix; do not strip it. The server's `/docs` and `/openapi.json` stay private unless deliberately exposed. See [Caddy proxy behavior](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy).

Verify from a different network: valid TLS, correct DNS including IPv6 if published, no database/internal storage ports reachable, and public health/readiness endpoints returning JSON. Hostname access must work from API containers too, unless a reviewed backchannel is configured.

## 6. Back up and prove recovery before cutover

Agree RPO/RTO with the recovery owner. For example, daily database snapshots imply up to 24 hours of lost changes; if that is unacceptable, schedule more frequent backups or PostgreSQL WAL archiving. This is a decision, not a default approval.

Back up the application database, identity database, identity signing/configuration data, private objects, Compose/proxy configuration and encrypted environment custody. Logical PostgreSQL backups can use the matching PostgreSQL tools, for example:

```sh
umask 077
docker compose exec -T database pg_dump -U monash -d monash --format=custom --no-owner --no-acl > application.dump
```

Capture a consistent set during a write pause or with a documented reconciliation point. Encrypt before transferring to independent off-server storage; retain the decryption key somewhere recoverable independently of the failed server. Monitor backup failures, age and storage growth. A successful dump is not a restore test.

Restore into a separate disposable environment, never over production. Verify database migrations, row counts, report ownership, identity sign-in, object counts/hashes and denied anonymous photo access. Measure lost-change window and recovery time. `scripts/staging_backup.py` documents a local rehearsal, but its fixed staging container/path names and bounded object handling make it unsuitable as an unmodified production backup scheduler.

## 7. Accept identity, data and capacity

Before changing Vercel, exercise these against the release environment with dedicated QA accounts:

1. Registration sends real mail, unverified users cannot acquire normal access, and recovery revokes old sessions.
2. A citizen can submit/retry a report and photo, view only their own history, and cannot moderate or run operator actions.
3. Grant an approved registered account capability by UUID using `scripts/administer_account.py` from the secured administration environment; record administrator/reason. Operator sign-in must produce verified MFA, then allow authorized work. Revoke and verify existing sessions lose access.
4. Moderation exposes only approved, privacy-reduced community data. Private notes/media and exact locations do not leak into public output.
5. Imported plant/lab records, filters, dates, units and below-detection handling reconcile to the approved source. Scenarios save/run and immutable results compare only compatible runs. Scientific outputs remain illustrative and unvalidated.
6. Measure representative concurrent reads, report/photo sizes and simulations; record error/latency/resource limits. Add and test request/upload limits without breaking valid photo submission or issuing duplicate writes on retries. The estimate of 20–50 people is not measured concurrency.
7. Alert an actual maintainer on readiness failure, elevated errors, disk pressure, backup age and certificate expiry. Verify a reboot preserves data and starts services.

## 8. Cut over Vercel only after acceptance

Keep browser requests same-origin: `https://water.example.com/api/v1/...` should proxy to `https://api.example.com/api/v1/...`. Keep `VITE_API_BASE` unset for the production browser; changing it to an external origin can break host-only session cookies, CSRF and the relative sign-in links.

In `apps/dashboard/vercel.json`, replace the inherited `https://wwtp-api.onrender.com/api/:path*` destination with the approved server API destination, preserving paths. Keep the API rewrite before the SPA fallback. Do not use a staging address. Configure provider/CDN caching so authenticated/API responses are never cached; inspect actual response headers.

Release a preview first. Test login through the **website-origin proxy**, callback, secure HTTP-only session cookie, CSRF cookie/header, logout, report upload/download, moderation and simulations. Ensure `/api/v1/plants` returns a JSON array, `/api/v1/monitoring/stations?offset=0&limit=1` returns a paginated JSON object and `/api/v1/ready` returns `{"status":"ready"}`. A `200` with HTML from the SPA fallback fails this check. A preview origin needs an explicitly allowed exact callback/origin or an isolated acceptance environment; do not temporarily add wildcard callbacks.

Record the release image digest, schema revision, frontend SHA, data reconciliation, backup checkpoint, acceptance owner and rollback triggers. Switch production, repeat smoke checks and observe the acceptance window. Prepare rollback **before** release: preserve/export writes since cutover, revert compatible client routing/images only, and do not blindly restore an old database. Keep legacy service/data available until migration acceptance closes. The existing Android APK remains on its old backend until a separately tested signed update ships.

## What to provide next

Provide the server OS/IP, chosen API/account domains, website origin, SSH access method, SMTP choice and S3 choice. Keep passwords/private keys in your secret manager or server custody. With those available, the production-specific Compose/identity setup can be prepared and tested; this guide alone does not deploy anything or close P0.

# Standalone server readiness

The public static website is published. Shared API/identity production deployment and client cutover are not complete. Start with independent dashboard/static hosting and API processes behind TLS, application PostgreSQL, authentik with a separate identity database, and private object storage. A shared physical server is acceptable initially; keep service credentials, database roles and backup procedures distinct.

Before deployment, record domains, TLS/DNS ownership, approved maintainers, measured request/photo volume, resource limits, API workers, object retention, RPO/RTO, and recovery owners. Use secret injection outside Git, restricted DB networking, least-privilege DB roles, durable object storage and versioned release artifacts. Migrations run as an explicit release step before traffic changes. Do not deploy the disposable Compose service or its credentials.

Current blockers:

- Identity, reporting/monitoring contracts, client cutover and privacy reconciliation remain planned.
- The inherited npm audit findings were remediated locally (MapLibre upgrade, removal of unused umbrella dependency, compatible lockfile updates). The current audit is clean; require the CI audit and browser release checks before deployment.
- Mobile release signing is inherited debug signing; production signing/distribution is pending.
- Simulation remains illustrative and unvalidated; scientific decision use is prohibited.
- Software licensing and actual CODEOWNERS assignments need owner decisions.

## Backup and restore gate

Application and identity PostgreSQL need independent encrypted backups with WAL/PITR appropriate to the agreed RPO. Include object data, configuration, encryption/signing keys and access policy in the recovery inventory. Monitor backup completion and retention; do not treat an untested dump as recovery evidence.

Before cutover, restore both databases and objects into an isolated environment. Verify schema revisions, row counts/checksums, account `(issuer, subject)` mappings, media references and access controls, then measure achieved recovery time and data loss. Record evidence and owner sign-off against RTO/RPO. No restore has been rehearsed by this foundation.

Release/cutover also needs health and dependency checks, error/latency/resource monitoring, structured logs with request IDs and redaction, authorization sampling, data reconciliation and load testing. Retain a pre-cutover backup and compatible prior artifacts; rehearse rollback and migration reversibility before disabling direct legacy writes. The [roadmap](../migration/ROADMAP.md) owns the sequencing.

## Public website — published 2026-10-03

Public URL: https://monash-water-platform.jienweng-lai.chatgpt.site

Hosting: Sites, public audience. Exact project/version/deployment and source identities are recorded in `public-site.json`. This deploy serves the current React frontend; it does not run FastAPI, PostgreSQL or authentik. `/download` remains unavailable for APK downloads, research has no approved publications yet, and shared account pages disclose unavailable integration. The operator client still uses legacy data endpoints; public hosting does not complete that API cutover.

The publishing checkout is a frontend-only mirror at `/home/jienweng/projects/monash-platform-public-site`, with its own `.openai/hosting.json` and Site source history. GitHub remains the canonical application source. Build output uses `static.directory: dist`; public redirects preserve React deep links. Private source reference directories, database content, keys and local env files are excluded from this mirror.

For updates:

1. Verify the canonical frontend commit and its tests/build. Review any change in build-time public configuration.
2. Open this same Site through the Sites hosting workflow and copy reviewed frontend source changes into its returned checkout; preserve its `.openai/hosting.json` and Site identity. Do not create another Site.
3. Install from the unchanged or revised lockfile as required; build from that exact source and push/package with the Sites workflow. Save the matching source SHA and archive as a new version, then deploy it with the existing public audience.
4. Require a succeeded deployment result and record its URL, version/deployment IDs and canonical source commit here. Rollback deploys a previously saved compatible Site version.

The full React operator bundles remain sizeable; public entry JavaScript is split from those routes. This static deployment is portable to a standalone TLS server later; provide SPA deep-link fallback and independent API/identity origins at cutover.

## APK publication state

No public production APK is published. Current CI compiles a debug APK against synthetic values; inherited `android/app/build.gradle.kts` also signs release mode with a debug key. Neither constitutes a production release. The installed local Flutter SDK is now 3.47.5; CI remains pinned to verified 3.44.7, so public builds must use a deliberate, recorded toolchain rather than silently changing it.

Required inputs: the intended operational backend/identity contract and approved public client configuration; a project-owned signing keystore or a decision to create a new signing identity; a secure key custody and recovery location; real Android installation/update evidence. Never send signing passwords through chat or commit keystores. A Supabase service key must never be included in an APK.

Once these are supplied, configure release signing, build and verify the signed APK, derive its version/minimum Android/size/SHA-256 metadata, install and update-test it, place the immutable APK on public HTTPS storage, and activate the validated website release manifest. The current download page already supports version metadata, release notes and checksum display. Hosting credentials or private GitHub repository links do not make an APK publicly downloadable.

References: [Flutter Android release guide](https://docs.flutter.dev/deployment/android), [Android signing](https://developer.android.com/studio/publish/app-signing), [Android developer verification](https://developer.android.com/developer-verification/guides). Check applicable target-region installation requirements at release time.

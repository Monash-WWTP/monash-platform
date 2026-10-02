# Standalone server readiness

The public static website is published. Shared API/identity production deployment and client cutover are not complete. Start with independent dashboard/static hosting and API processes behind TLS, application PostgreSQL, authentik with a separate identity database, and private object storage. A shared physical server is acceptable initially; keep service credentials, database roles and backup procedures distinct.

Before deployment, record domains, TLS/DNS ownership, approved maintainers, measured request/photo volume, resource limits, API workers, object retention, RPO/RTO, and recovery owners. Use secret injection outside Git, restricted DB networking, least-privilege DB roles, durable object storage and versioned release artifacts. Migrations run as an explicit release step before traffic changes. Do not deploy the disposable Compose service or its credentials.

Current blockers:

- Identity, reporting/monitoring contracts, client cutover and privacy reconciliation remain planned.
- The inherited npm audit findings were remediated locally (MapLibre upgrade, removal of unused umbrella dependency, compatible lockfile updates). The current audit is clean; require the CI audit and browser release checks before deployment.
- Mobile release signing uses a project-owned key; see `android-direct-release.md` for custody and verification.
- Simulation remains illustrative and unvalidated; scientific decision use is prohibited.
- Software licensing and actual CODEOWNERS assignments need owner decisions.

## Backup and restore gate

Application and identity PostgreSQL need independent encrypted backups with WAL/PITR appropriate to the agreed RPO. Include object data, configuration, encryption/signing keys and access policy in the recovery inventory. Monitor backup completion and retention; do not treat an untested dump as recovery evidence.

Before cutover, restore both databases and objects into an isolated environment. Verify schema revisions, row counts/checksums, account `(issuer, subject)` mappings, media references and access controls, then measure achieved recovery time and data loss. Record evidence and owner sign-off against RTO/RPO. No restore has been rehearsed by this foundation.

Release/cutover also needs health and dependency checks, error/latency/resource monitoring, structured logs with request IDs and redaction, authorization sampling, data reconciliation and load testing. Retain a pre-cutover backup and compatible prior artifacts; rehearse rollback and migration reversibility before disabling direct legacy writes. The [roadmap](../migration/ROADMAP.md) owns the sequencing.

## Previous Sites deployment — 2026-10-03

Public URL: https://monash-water-platform.jienweng-lai.chatgpt.site

Hosting: Sites, public audience. Exact project/version/deployment and source identities are recorded in `public-site.json`. This deploy serves the current React frontend; it does not run FastAPI, PostgreSQL or authentik. `/download` remains unavailable for APK downloads, research has no approved publications yet, and shared account pages disclose unavailable integration. The operator client still uses legacy data endpoints; public hosting does not complete that API cutover.

The publishing checkout is a frontend-only mirror at `/home/jienweng/projects/monash-platform-public-site`, with its own `.openai/hosting.json` and Site source history. GitHub remains the canonical application source. Build output uses `static.directory: dist`; public redirects preserve React deep links. Private source reference directories, database content, keys and local env files are excluded from this mirror.

For updates:

1. Verify the canonical frontend commit and its tests/build. Review any change in build-time public configuration.
2. Open this same Site through the Sites hosting workflow and copy reviewed frontend source changes into its returned checkout; preserve its `.openai/hosting.json` and Site identity. Do not create another Site.
3. Install from the unchanged or revised lockfile as required; build from that exact source and push/package with the Sites workflow. Save the matching source SHA and archive as a new version, then deploy it with the existing public audience.
4. Require a succeeded deployment result and record its URL, version/deployment IDs and canonical source commit here. Rollback deploys a previously saved compatible Site version.

The full React operator bundles remain sizeable; public entry JavaScript is split from those routes. This static deployment is portable to a standalone TLS server later; provide SPA deep-link fallback and independent API/identity origins at cutover.

## APK publication state before the direct-release work

No public production APK is published. Current CI compiles a debug APK against synthetic values; inherited `android/app/build.gradle.kts` also signs release mode with a debug key. Neither constitutes a production release. The installed local Flutter SDK is now 3.47.5; CI remains pinned to verified 3.44.7, so public builds must use a deliberate, recorded toolchain rather than silently changing it.

Required inputs: the intended operational backend/identity contract and approved public client configuration; a project-owned signing keystore or a decision to create a new signing identity; a secure key custody and recovery location; real Android installation/update evidence. Never send signing passwords through chat or commit keystores. A Supabase service key must never be included in an APK.

Once these are supplied, configure release signing, build and verify the signed APK, derive its version/minimum Android/size/SHA-256 metadata, install and update-test it, place the immutable APK on public HTTPS storage, and activate the validated website release manifest. The current download page already supports version metadata, release notes and checksum display. Hosting credentials or private GitHub repository links do not make an APK publicly downloadable.

References: [Flutter Android release guide](https://docs.flutter.dev/deployment/android), [Android signing](https://developer.android.com/studio/publish/app-signing), [Android developer verification](https://developer.android.com/developer-verification/guides). Check applicable target-region installation requirements at release time.

## Primary website: Vercel — 2026-10-03

URL: https://monash-water-platform.vercel.app

The user chose Vercel as primary hosting. This is a new `monash-water-platform` project under the authenticated `lai-jien-wengs-projects` team; the legacy `wwtp-dashboard` project and domain are preserved. Project/deployment IDs and exact frontend source commit are recorded in `public-site.json`. The earlier Sites deployment remains a previous snapshot; future hosting changes target Vercel.

Vercel configuration:

- Root directory: `apps/dashboard`; framework: Vite; Node: 22.x.
- Install: `npm ci`; build: `npm run build`; output: `dist`.
- The inherited `/api/:path*` rewrite to `https://wwtp-api.onrender.com/api/:path*` is preserved during legacy client migration; the following SPA fallback serves public/plant deep links. This proxy does not run the successor API or establish shared accounts.
- `.vercelignore` anchors unrelated directories to the repository root. Unanchored names such as `research/` would incorrectly remove the frontend's `src/research` directory. Local dependencies, outputs, env files and signing material are excluded. Vercel local project state and OIDC env files are ignored by Git.

Deploy from the repository root using authenticated Vercel CLI:

```sh
npx --yes vercel@62.2.0 link --project monash-water-platform --scope lai-jien-wengs-projects
npx --yes vercel@62.2.0 deploy --prod --yes --scope lai-jien-wengs-projects
```

The remote project root/build settings must match the values above. Verify deployment is READY, then check unauthenticated public routes and local assets. Never infer public accessibility from a protected deployment URL. Keep API/identity/database hosting separate and use independent public APK object storage when the signed artifact is ready.

GitHub automatic deployment is not connected: Vercel could not access the private `Monash-WWTP/monash-platform` organization repository. Grant the Vercel GitHub integration access to this repository, then connect this same Vercel project and select `apps/dashboard`. Manual CLI production publishing already works. No account token has been committed or copied into GitHub Actions secrets.

## Current direct Android release, 2026-10-03

CitizenFlood 1.0.0 (versionCode 2) is signed with the project release identity and publicly hosted at the immutable URL recorded in `android-release-1.0.0.json`. Unauthenticated download size and SHA-256 matched the verified APK. Fresh Android 16 emulator installation, live-backend startup and same-version reinstall passed; physical-device and cross-version update tests remain unperformed. No synthetic reports were submitted. The dashboard release manifest activates the download link. Shared accounts/standalone API remain future work. See `android-direct-release.md` for signing custody and reproduction.

# Continue on a new machine

Handoff date: 21 October 2026. This guide assumes a Linux shell; adapt installation and Android USB setup for the new operating system. No repository clone, developer tools or credentials are assumed to exist there.

## Current source of truth

- Main repository: https://github.com/Monash-WWTP/monash-platform
- Public documentation repository: https://github.com/Monash-WWTP/monash-platform-docs (optional for application/backend work; clone when updating the published manual).
- PR #11 merged shared account settings, map-first mobile reporting and operator response. PR #12 merged its small analyzer correction.
- Verified `main` at handoff: `e455276`; GitHub api, citizenflood, dashboard and inventory checks all passed. Fetch current `main` on the new machine; do not resume the obsolete `feat/mobile-map-first` branch or reopen merged PRs.
- Latest local acceptance: 209 Python tests passed/1 skipped, 59 Flutter tests, 50 dashboard tests and 15 tests inside pinned authentik. Analyzer/lint/builds passed. Migration head: `b72a05e3c114`.
- The former worktree was `/home/jienweng/projects/monash-platform-interface-launch`. This path and its SDK locations are machine-specific, not setup requirements.

## 1. Install tools and clone

Install Git, GitHub CLI, Docker Engine/Desktop with Compose, Python 3.12 with uv, Node.js 22/npm, Flutter 3.44.7 stable, JDK 21, and Android Studio/SDK/platform-tools. Android SDK platforms 35/36 and build-tools 36.0.0 were used. Run Docker and ensure your account may use it. Install from official distributions; use committed lockfiles rather than upgrading dependencies during onboarding.

Authenticate using GitHub CLI's interactive browser flow. Never paste passwords, tokens or keys into chat or committed files.

```sh
gh auth login
gh auth status
mkdir -p ~/projects
cd ~/projects
gh repo clone Monash-WWTP/monash-platform
cd monash-platform
git switch main
git pull --ff-only
git status --short
```

Git alone also works: `git clone https://github.com/Monash-WWTP/monash-platform.git`. Private-repository access must be granted to the developer's GitHub account first.

For the manual, separately run `gh repo clone Monash-WWTP/monash-platform-docs` from `~/projects`, then follow that repository's own README and lockfiles. Do not invent its install command from this repository.

Read before editing: `AGENTS.md`, `CONTRIBUTING.md`, `docs/migration/ROADMAP.md`, `docs/science/VALIDATION.md`, `docs/operations/local-development.md`, and the README of the affected app. Use CodeGraph first only if a `.codegraph/` index exists; do not create one automatically. Start new work on a new feature branch/worktree from current `main`.

## 2. Verify a fresh checkout

```sh
uv python install 3.12
uv sync --locked --python 3.12
node --version
java -version
flutter --version
flutter doctor -v
flutter doctor --android-licenses
```

Accept Android licenses on the new machine. Confirm Flutter is exactly 3.44.7 and JDK is 21. Configure the new machine's SDK path locally; do not commit `android/local.properties`, generated build output or machine-specific paths.

### Disposable API test database

These tests reverse/reapply schema. Use only the disposable test database on port 5433, never the staging database on 5544 or a production database. The credentials below are deliberately public disposable test values.

```sh
docker compose -f infra/local/compose.test.yaml up -d --wait db
export DATABASE_URL='postgresql+psycopg://monash_test:monash_test@127.0.0.1:5433/monash_test'
export TEST_DATABASE_URL="$DATABASE_URL"
export APP_ENV=test
uv run --locked alembic -c services/api/alembic.ini upgrade head
uv run --locked alembic -c services/api/alembic.ini check
uv run --locked pytest -q tests services/api/tests packages/simulation/wwtp_sim/tests
uv run --locked python scripts/export_openapi.py
git diff --exit-code -- services/api/openapi.json
uv run --locked python scripts/check_repository.py
uv run --locked python scripts/check_import_inventory.py --verify-targets
unset DATABASE_URL TEST_DATABASE_URL APP_ENV
```

The inventory check verifies imported targets. External legacy source checkouts are optional unless performing full original-source reconciliation; they are not required to run the current application.

### Dashboard and mobile checks

```sh
cd apps/dashboard
npm ci
npm test
npm run lint
npm run build
cd ../citizenflood
flutter pub get
flutter analyze
flutter test
flutter build apk --debug --dart-define-from-file=staging-config.example.json
cd ../..
```

Debug artifact: `apps/citizenflood/build/app/outputs/flutter-apk/app-debug.apk`. It targets local staging and is not the public release package.

## 3. Start the complete local development stack

This starts a new synthetic development environment. Git does not carry the old databases, objects, local secrets or QA accounts. `scripts/staging.py` creates owner-only local secrets when absent and preserves them afterward. Do not regenerate or mix credentials with an existing restored volume.

From the repository root:

```sh
python3 scripts/staging.py up -d --wait database identity-db mail storage identity-server identity-worker
```

Allow the identity service's first migrations to finish. Confirm the following returns HTTP 200 before provisioning its flows:

```sh
curl --fail --silent --output /dev/null http://localhost:9100/api/v3/root/config/
```

Then provision the branded local flows and build/start the API:

```sh
python3 scripts/staging.py exec -T identity-server ak shell -c "exec(open('/monash-brand/bootstrap.py').read())" > /tmp/monash-identity-bootstrap.log 2>&1
python3 scripts/staging.py exec -T identity-server ak shell -c "exec(open('/monash-brand/tests/test_account_settings.py').read())" > /tmp/monash-identity-tests.log 2>&1
docker build -f services/api/Dockerfile -t monash-api:local .
python3 scripts/staging.py up -d api
curl --fail http://localhost:8181/api/v1/ready
```

The Compose migration service upgrades the local staging database before API startup. If bootstrap or tests fail, inspect the local logs without publishing secrets, verification links or MFA material. Bootstrap is **local-only**, with localhost endpoints and test email; never run it unchanged in production. Avoid `scripts/staging_api.py identity` on a fresh machine: its legacy log location/hard-coded container assumptions are not needed by the commands above.

If the new staging database needs the public plant/station snapshot, use the explicit idempotent importer:

```sh
python3 scripts/staging_api.py import
```

This imports only the checked-in public snapshot; restricted legacy data requires separate authorized migration. The API image has no Compose build configuration: after API source edits, run `docker build` again before recreating `api`; `up --build` alone does not rebuild this image.

In a separate terminal:

```sh
cd ~/projects/monash-platform/apps/dashboard
npm run dev -- --host 127.0.0.1 --port 8180 --strictPort
```

| Service | Local address | Purpose |
| --- | --- | --- |
| Web | http://localhost:8180 | Public site, dashboard and `/account` |
| API | http://localhost:8181/api/v1 | Shared versioned service; `/ready` checks dependencies |
| Identity | http://localhost:9100 | Branded account flows and OIDC |
| Mailpit | http://localhost:8125 | Development verification/recovery mail only |
| Private storage | http://localhost:3900 | Local S3-compatible photos |
| Staging PostgreSQL | 127.0.0.1:5544 | Development application data; never run destructive tests here |
| Disposable PostgreSQL | 127.0.0.1:5433 | Schema/API test suite only |

Use **localhost:8180** in the browser, not `127.0.0.1:8180`, for sign-in: the registered OIDC callback is localhost. Vite proxies `/api` to the local API. Create a new clearly synthetic account through registration; read its mail in Mailpit. Do not assume an old QA account exists. Operator/admin permissions are server-granted and operator actions require MFA; ordinary registration must not grant them. Follow the approved administration runbook/CLI rather than editing permissions through an unreviewed shortcut.

## 4. Connect and verify the Samsung

Enable Developer options and USB debugging, connect a data cable, unlock the phone and accept the new computer's debugging authorization. No PIN or password needs to be shared.

```sh
adb devices
adb reverse tcp:8181 tcp:8181
adb reverse tcp:9100 tcp:9100
adb install -r apps/citizenflood/build/app/outputs/flutter-apk/app-debug.apk
adb shell am start -n au.edu.monash.citizenflood.staging/au.edu.monash.citizenflood.MainActivity
```

The staging package is `au.edu.monash.citizenflood.staging`. Physical-device localhost is the phone itself; USB reverse and running local services are required. Reverse mappings may disappear when ADB restarts or the cable reconnects.

A fresh machine normally has a different Android debug signing key. If reinstall reports `INSTALL_FAILED_UPDATE_INCOMPATIBLE`, do not uninstall automatically: that erases the staging app's local data/drafts. Either transfer the old development debug keystore securely for continuity, or obtain the user's approval to remove only the staging package and reinstall. This is separate from the protected project **release** signing identity. Never commit either keystore.

Use a synthetic account to verify sign-in returns to CitizenFlood, map/report selection, original/update forms and private photo submission. Keep QA observations Pending/unpublished. For account testing, open Profile, reauthenticate, edit its optional label, return to the app and verify refreshed details. Check cancellation, revoked sessions and network failure without changing human credentials. The previous machine passed this Profile round-trip and inspected portrait bubble placement and tap-to-select coordinates.

## 5. What is implemented

- Green map-first CitizenFlood with Map/My reports/Account, separate icon bubbles, tap/current-location selection, explicit review and privacy generation fences.
- Versioned citizen-observation protocols, contextual optional measurements, photo provenance and linked flooding updates. Legacy meanings remain intact. Citizen observations are not silently treated as laboratory measurements or simulation inputs.
- MFA-protected operator assignment, inspection, actions, closure/reopening and audit history, separate from publication approval and scientific validation.
- Shared Profile, verified email/password and Security controls in app/web; recent-authentication guards and signed revocation events; no duplicate password database or client-side permission grants.
- All four account emails inherit `infra/staging/identity/templates/email/monash_base.html`, sharing logo/layout/button/footer while retaining distinct confirmation/recovery/change wording.
- Administration source for users/permissions, plant/station settings, versioned factors/thresholds, audit and status. Production deployment remains pending.

Evidence and implementation references:

- `docs/operations/shared-account-settings.md`
- `docs/operations/operator-response.md`
- `docs/operations/platform-administration.md` and `scripts/administer_account.py` (trusted grants)
- `docs/operations/citizen-observation-protocol.md`
- `docs/operations/samsung-mobile-acceptance-2026-10-20.md`
- `docs/operations/mobile-ux-checklist.md`
- `docs/product/platform-resolution-checklist.md`
- `docs/superpowers/specs/` and `docs/superpowers/plans/` (approved designs/plans)

## 6. Continue in this order

1. **Restore a green fresh-machine baseline** using this guide. Check current GitHub CI and repository status before changing anything. Do not repeat already merged implementation.
2. **Complete remaining mobile acceptance:** TalkBack/reading order, landscape/keyboard, denied GPS/camera permissions, offline/background/resume, slow-network recovery and measured release/profile performance. Preserve concise wording and the existing green app/dashboard/landing colors; docs remain neutral.
3. **Optional small correctness follow-up:** display-name projection can race when older/newer signed proofs arrive concurrently. Serialize/conditionally update `profile_claim_iat` and label, with a real concurrency regression. This affects an optional display label, not identity keys or permissions. Same-second labels may also require a later refresh.
4. **Plan map growth separately:** current recent-feed bounds are not viewport pagination/clustering. Add a shared bounded viewport API and appropriate mobile/dashboard clustering only through an approved design. Place search needs an approved geocoder and privacy/coverage choice; no provider has been selected.
5. **Production provisioning when access exists:** the user has not provisioned a server. Obtain approved host/provider, API/account HTTPS domains, SMTP, private storage and credential custody through secure channels. Do not invent domains or deploy local Compose/localhost flows unchanged. Use `docs/operations/production-server-setup.md` and the resolution checklist; qualify migrations, permissions, email delivery, uploads, monitoring, backup/restore and rollback.
6. **Public APK only after production integration:** configure approved production API/OIDC values, test on the Samsung over mobile data without USB reverse, build/sign with the existing release identity, verify installation/update/hash, then update the public download. See `docs/operations/android-direct-release.md` and `scripts/build_android_release.py`. A debug APK can be rebuilt before provisioning, but its local-only service configuration is unsuitable for public use. The published signed APK has not been replaced by this work.
7. **Research/operations acceptance remains separate:** validate protocol usability and measurement quality in the field, assign accountable scientific/operational owners and document limitations. Tests do not authorize scientific decision use or automatic plant control.

Unified per-device mobile/API session management remains deferred. Native provider Sessions shows its actual scope; Sign out all devices is the broader revocation control. Initial admin grants and secrets remain server-only. Do not add account merging by email, automatic control, production warnings or verbose product banners without a concrete approved requirement.

## 7. Transfer data and custody deliberately

A source clone is enough for a new synthetic development environment. It does **not** reproduce the old local identities, reports, photos or credentials.

For continuity, the owner must arrange an encrypted, access-controlled transfer of the application database, identity database, private objects and corresponding configuration/key material together. Read `scripts/staging_backup.py` and the backup/restore runbook before executing a backup. Preserve issuer/subject UUID mappings; recreating a user with the same email does not preserve identity or report ownership. Do not put backups, `.env.local`, `garage.toml.local`, QA credential files, signing keys, tokens, verification URLs or MFA seeds in Git, PRs or chat.

Release signing custody must be transferred separately by its owner if this machine will publish updates. Without the existing signing identity, do not substitute a new key for an update to the existing release.

## 8. Shutdown and previous-machine state

The previous machine's Monash staging services and disposable PostgreSQL were stopped; named volumes and owner-only local configuration were retained. No data/volumes were deleted. The staging phone app was closed, task USB reverse mappings removed, keep-awake disabled and the task ADB server stopped. No project Vite/HTTP preview process was running at shutdown. Unrelated projects' containers were left alone.

On the new machine, stop foreground Vite with Ctrl+C. Stop local containers without deleting their volumes:

```sh
python3 scripts/staging.py --profile api down
docker compose -f infra/local/compose.test.yaml down
adb reverse --remove tcp:8181
adb reverse --remove tcp:9100
adb shell svc power stayon false
```

Do not add `-v`, prune Docker volumes, uninstall the app or reset databases as routine shutdown.

## Prompt for the next coding agent

> Read AGENTS.md, CONTRIBUTING.md and docs/operations/next-machine-handoff-2026-10-21.md in a fresh clone of Monash-WWTP/monash-platform. PRs11/12 are merged; start from current main and verify its actual state. Restore the local synthetic development environment and a green baseline first. Continue the remaining mobile acceptance checklist, then address the documented optional display-label concurrency issue if requested. Production provisioning and public signed APK replacement remain pending approved infrastructure/custody. Keep the existing green product design, concise wording, shared branded email base, immutable identity/report ownership and separate scientific validation. Do not copy secrets into chat or Git, recreate old ownership by email, rerun destructive tests against staging, or redo completed features. Report what is verified versus still pending.

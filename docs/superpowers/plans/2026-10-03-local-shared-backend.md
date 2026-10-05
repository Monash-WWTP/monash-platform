# Local Shared Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the shared platform locally with real monitoring data, shared identity, reporting/media/moderation, reproducible simulations, migrated clients and recovery evidence.

**Architecture:** A modular FastAPI application owns application PostgreSQL and private object storage. authentik provides shared OIDC identity with separate persistence. Local staging remains isolated from deployed Supabase clients; deployment and production cutover happen later.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic, PostgreSQL, authentik, S3-compatible storage, React/TypeScript, Flutter/Dart, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-10-02-shared-platform-architecture-design.md`; authorized local execution and `docs/operations/backend-release-plan.md` narrow deployment to local staging.

## Global Constraints

- No invented operational reports or measurements; test fixtures remain in isolated test databases.
- Preserve real public CSV content, source identifiers, BDL flags, units and provenance.
- Accounts map `(issuer, subject)`; email cannot claim anonymous reports.
- Verified citizen registration; invited operator capabilities and MFA.
- Public observations omit identity, notes, precise coordinates and private media paths.
- One application migration chain; identity schema separate.
- Scientific model remains `illustrative_unvalidated`, `decision_use_permitted=false`.
- Existing published website/APK continue using current production services until deployment.
- No credentials/build artifacts/private exports in Git; pinned toolchains and lockfiles.

## Review Focus

- Token issuer/audience/signature/expiry and identity outage fail closed (Task 2).
- Cross-owner and cross-capability report/media access is rejected (Task 4).
- Duplicate submission/import retries cannot duplicate records or silently rewrite provenance (Tasks 3/4).
- Scenario edits/deletes cannot alter retained run evidence (Task 5).
- Backup restoration and old anonymous ownership are reconciled before any cutover (Tasks 3/7).

### Task 1: Local runtime and readiness
**Files:** `infra/staging/compose.yaml`, `infra/staging/.env.example`, `services/api/Dockerfile`, `services/api/app/routers/readiness.py`, `services/api/tests/test_readiness.py`, `scripts/staging.py`.
**Interfaces:** app database on private network; API readiness at `/api/v1/ready`; local-only published ports.
- [ ] Write readiness tests: usable migrated DB returns 200; absent DB/schema returns 503 without leaking credentials.
- [ ] Run tests and observe missing-route failure.
- [ ] Implement readiness and pinned runtime with once-per-release migrations and no seed on startup.
- [ ] Run baseline/full tests and boot fresh local database with migrations.
- [ ] Commit with verification evidence.

### Task 2: Shared identity and roles
**Files:** `services/api/app/identity/`, `services/api/app/routers/auth.py`, `services/api/app/db/platform.py`, new Alembic revision, `services/api/tests/test_identity.py`, `infra/staging/identity/`.
**Interfaces:** verified OIDC principal and capability dependencies; browser server-side session/cookie/CSRF; mobile bearer tokens using same issuer; account roles in application DB.
- [ ] Test invalid signature/issuer/audience/expiry, unverified account, role separation and CSRF/session expiry.
- [ ] Observe failure; implement OIDC validation, PKCE browser callback/state/nonce and persisted sessions.
- [ ] Configure real local authentik providers, verified enrollment, invitations/MFA and local email delivery capture.
- [ ] Verify live provider metadata, login/recovery/role behavior and tests; record local-only capture mail limitation.
- [ ] Commit.

### Task 3: Monitoring and real migration
**Files:** `services/api/app/monitoring/`, `services/api/app/migration/`, `services/api/app/routers/monitoring.py`, `scripts/migrate_platform.py`, `services/api/tests/test_monitoring.py`, `services/api/tests/test_migration.py`.
**Interfaces:** paginated stations/samples/year/filter API; source manifest/hash import and reconciliation; private export schema preserving legacy report subjects.
- [ ] Test exact real snapshot counts/IDs/BDL/nulls, retries, changed source rejection and private projection.
- [ ] Observe failures; implement transactional allowlisted import with provenance and no guessed capacity/permit data.
- [ ] Import the real 1-station/154-sample snapshot into staging and reconcile hashes/counts.
- [ ] Prepare private report/photo importer; run only with authorized source, keep originals and anonymous ownership unclaimed.
- [ ] Commit evidence; missing private export remains explicitly recorded, never replaced with fixtures.

### Task 4: Reports, private media, moderation
**Files:** `services/api/app/reporting/`, `services/api/app/routers/reports.py`, `services/api/tests/test_reporting.py`, `services/api/tests/test_media.py`.
**Interfaces:** owner reports/history, idempotency key, bounded image upload, scoped read, moderation audit and approved coarse public projection.
- [ ] Test verified ownership, category/unit constraints, retries/conflicts, foreign media, size/type limits and privacy.
- [ ] Observe failures; implement transactional submissions, storage verification and role-gated audited moderation.
- [ ] Verify failures cannot claim stored media or approved status; exercise storage integration without real fabricated reports.
- [ ] Commit.

### Task 5: Immutable simulation evidence
**Files:** `services/api/app/db/models.py`, `services/api/app/services/simulation.py`, existing scenario/run routers/schemas, Alembic revision, `services/api/tests/test_run_provenance.py`.
**Interfaces:** immutable snapshots/validation status/start date/artifact digest and durable failed runs; scenario deletion archives.
- [ ] Test replay determinism, snapshot retention after edit/delete and failed runs without KPI output.
- [ ] Observe failures; implement snapshots and archive semantics without inventing historical snapshots.
- [ ] Run existing model golden tests and full API tests; regenerate OpenAPI.
- [ ] Commit.

### Task 6: Both clients and API contracts
**Files:** dashboard API/auth/monitoring/public account routes and moderation UI; CitizenFlood config/auth/report/media/profile flows; generated contracts and contract checks.
**Interfaces:** `/api/v1` API, browser HTTP-only session and CSRF, Android PKCE/secure storage, stable report wire fields.
- [ ] Write contract/access tests and observe current legacy-route failures.
- [ ] Implement backend-only clients with shared account login and clear errors; preserve public research/APK delivery.
- [ ] Verify React tests/lint/build/browser and Flutter analyze/test/build and Android local-provider flow.
- [ ] Keep published APK immutable; build local staging app separately, never ship localhost endpoints publicly.
- [ ] Commit.

### Task 7: Recovery and local acceptance
**Files:** `scripts/staging_backup.py`, `scripts/staging_acceptance.py`, `docs/operations/local-staging.md`, migration/recovery records.
**Interfaces:** restricted backup bundle, app/identity/media restore into separate local stack, reproducible acceptance report.
- [ ] Test wrong-target refusal, backup checksums and restore reconciliation; observe failures.
- [ ] Implement backups/restore and local bounded load/health tests with redacted logs.
- [ ] Rehearse real snapshot restore and record account/media limitations accurately; no production endpoint switches.
- [ ] Verify full suite/OpenAPI/client builds, run fresh whole-branch review, fix material findings and document remaining external gates.
- [ ] Commit final evidence and handover.

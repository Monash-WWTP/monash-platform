# Interface and Launch Readiness Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement the repository tasks task-by-task. Track acceptance evidence separately from implementation. Production cutover is a separate release decision.

**Goal:** Remove misleading UI states, improve everyday usability, and establish evidence for a shared-platform production release.

**Architecture:** Preserve the current public visual identity and independently deployed web, API, identity and Android boundaries. Deliver interface corrections first, then validate the existing shared backend in staging, then qualify production and client releases. Do not rebuild capabilities that already exist.

**Tech Stack:** React, TypeScript, Vite, MapLibre, ECharts, FastAPI, PostgreSQL/Alembic, authentik OIDC, private S3-compatible storage, Flutter Android.

**Spec:** Existing requirements in `PRODUCT.md`, `DESIGN.md`, `docs/product/platform-resolution-checklist.md`, `docs/science/VALIDATION.md`, and the interface/backend audit in this conversation dated 2026-10-18. This plan proposes targeted refinements, not a replacement visual design.

## Global constraints

- Keep public pages white/charcoal/deep green with self-hosted Manrope; preserve current product facts and approved-only research.
- Missing measurements remain missing. Citizen reports, laboratory samples and model outputs remain distinct.
- Simulation remains `illustrative_unvalidated` and `decision_use_permitted=false`.
- Preserve the published legacy APK; source changes do not update that artifact.
- Never switch production endpoints merely to make source and configuration appear consistent.
- Use only the disposable database specified in `docs/operations/local-development.md` for destructive test fixtures.
- Do not publish, cut over production, submit synthetic production reports, or modify identity/provider accounts during repository-only work.

## Baseline and limitations

Audit verification: frontend 12 tests, lint and build passed; Python suite had 92 passed, 1 failed, 1 skipped. The failure was `test_dashboard_snapshot_matches_pinned_frontend` for `apps/dashboard/index.html`. Repository policy and source-manifest target checks passed. Large operator chunks remain. T3 preview could not reach the local server; older captures inform visual direction but are not current visual acceptance.

## Review focus

1. All measurements missing/below detection: never manufacture zero-valued summaries (Task 1).
2. API outage or expired session: distinguish unavailable data from empty results and provide recovery (Tasks 1, 3, 5).
3. Keyboard-only and 320px-wide use: plant selection and panel dismissal remain accessible (Task 3).
4. Registration unavailable: no primary action promises a working registration flow (Task 2).
5. Lost responses and security changes: retries avoid duplicates; revoked identities cannot retain access (Task 5).

## Delivery order

Tasks 1–4 are a reviewable interface/repository batch. Tasks 5–6 form a separate backend qualification batch. Task 7 is production release work, dependent on the preceding evidence. Cosmetic changes must not delay the correctness fixes.

### Task 1: Correct monitoring summaries and failure states

**Files:** Modify `apps/dashboard/src/components/monitoring/StationDashboard.tsx`; create `apps/dashboard/src/components/monitoring/sampleSummary.ts` and `apps/dashboard/tests/sample-summary.test.ts`; modify `scripts/smoke_dashboard_map.py` for existing synthetic-state coverage where useful.

**Interfaces:** `summarizeMetric(samples: Sample[], metric: string): { totalCount: number; quantifiedCount: number; mean: number | null; max: number | null }`, using the existing monitoring sample type. Below-detection and null readings are excluded from quantified statistics; their underlying records are preserved.

- [ ] Add failing tests: empty/all-null/all-BDL return null mean/max and zero quantified count; mixed values `[2, 4]` plus null/BDL return mean 3/max 4 and accurate counts; measured zero remains zero.
- [ ] Run `npm --prefix apps/dashboard test` and confirm the new assertions fail before implementation.
- [ ] Implement the helper and render unavailable summaries as “No quantifiable readings”; display usable/total counts and explain exclusion of below-detection results without inventing a censoring method.
- [ ] Handle `useSamples` errors before empty states; provide Retry that preserves filters and selected metric.
- [ ] Verify synthetic empty, outage, all-BDL and mixed states; run frontend tests, lint and build. Commit the focused change.

### Task 2: Make public actions honest and simplify the homepage

**Files:** Modify `apps/dashboard/src/pages/public/{LandingPage,PublicLayout,AccountPage}.tsx`, `apps/dashboard/src/pages/public/public.css`, and `scripts/smoke_public_portal.py`; update `DESIGN.md` only for intentional changes.

**Interfaces:** Preserve `/login` and `/register` URLs. While shared identity is unavailable publicly, navigation says “Account availability”; the destination explains status without a disabled primary registration action. Keep CitizenFlood download the principal home action and dashboard the secondary action.

- [ ] Update the public route contract to detect misleading registration CTAs and require the availability explanation.
- [ ] Reduce repeated homepage download/dashboard promotions; use the existing release-appropriate app screenshot when its provenance and caption match the published artifact. Do not introduce fabricated metrics, imagery or claims.
- [ ] Tighten the mobile header so unavailable accounts do not dominate it. Preserve keyboard focus, skip link and logical reading order.
- [ ] Inspect current desktop and narrow-screen captures through T3 preview; check primary actions, wrapping, contrast and keyboard order. If preview remains unreachable, record visual acceptance as open.
- [ ] Run frontend tests, lint/build and the public contract through the permitted browser workflow. Commit.

### Task 3: Make monitoring practical with keyboard and mobile

**Files:** Modify `apps/dashboard/src/pages/MapPage.tsx` and `scripts/smoke_dashboard_map.py`.

**Interfaces:** Keep station selection and workspace URLs. Expose a plant list independent of WebGL availability; list search filters by plant name/code without changing the API contract. Both markers and list buttons open the same selected station.

- [ ] Add regression cases for keyboard selection, search with no matches, Escape/close dismissal, focus return and a 320px viewport.
- [ ] Replace clickable plant divs and interpolated `innerHTML` with named buttons and safe text nodes. Give close/expand controls accessible labels and adequate touch targets.
- [ ] Make the panel fit its viewport, preserve a usable scroll area, move focus into it on open and return focus on close.
- [ ] Honor reduced motion; remove `essential: true` from decorative camera flights and shorten normal navigation motion.
- [ ] Replace the port-8000 diagnostic with a user-facing unavailable message and Retry. Verify error versus empty data and map-unavailable fallback.
- [ ] Run frontend verification and browser checks; inspect desktop/mobile in one bounded review pass and one confirmation pass after fixes. Commit.

### Task 4: Restore a green baseline and reduce loading cost

**Files:** Inspect `apps/dashboard/index.html`, `tests/test_client_imports.py`, `docs/migration/IMPORT_ADAPTATIONS.md`, `apps/dashboard/src/components/ui.tsx`, chart/3D imports, and `apps/dashboard/vite.config.ts`.

**Interfaces:** Keep public/operator route splitting; preserve the pinned-source check's protection against undocumented adaptations.

- [ ] Explain the index.html difference against its pinned source. If intentional, document it and add the precise adaptation entry; if accidental, restore the intended file. Do not weaken hash checking globally.
- [ ] Capture route transfer sizes and loading behavior from the production build before changes; identify the actual source of the large shared UI chunk before choosing a bundling fix.
- [ ] Load chart/3D features when requested and remove broad imports only where they pull unused code into a route. Avoid dependency upgrades without a demonstrated need.
- [ ] Verify public routes do not request operator assets; verify charts, map workers and workspace still load. Record before/after route transfer sizes and loading measurements rather than relying on chunk count.
- [ ] Run the full documented Python suite, migrations/schema check, frontend tests/lint/build, OpenAPI drift check and both repository checkers. Commit once green.

### Task 5: Qualify existing shared backend in staging

**Files:** Use `infra/staging/compose.yaml`, `scripts/staging.py`, `scripts/staging_identity_acceptance.py`, `scripts/staging_operator_acceptance.py`, `scripts/staging_backup.py`, `services/api/tests/`, and both source clients. Record redacted evidence in `docs/operations/staging-acceptance-2026-10-18.md`.

**Interfaces:** Existing `/api/v1` contracts, browser cookie/CSRF flow, Android OIDC PKCE flow and issuer/subject account mapping remain authoritative. Extend the existing acceptance scripts rather than duplicating them.

- [ ] Run isolated staging from its documented configuration, record source SHA/schema/toolchain and distinguish synthetic fixtures from authorized real imports.
- [ ] Verify registration/email verification/recovery; operator invitation/MFA; citizen/operator separation; logout, expiry, revocation, provider outage and direct unauthorized requests.
- [ ] Exercise report submission, same-key retries after a lost response, photo validation/ownership, moderation and privacy-safe community output. Check that approval never exposes notes, exact location or private media.
- [ ] Verify lab filters, pagination, scenario edits/deletes, immutable successful/failed runs and comparisons through the actual dashboard. Verify source Android submission/history through the same API.
- [ ] Review request-rate/concurrency controls and database connection timeouts. Add missing controls with focused regression tests and measured limits; do not treat the current body-size limit as a rate limiter.
- [ ] Record each check's command, expected outcome, result and evidence; fix failures in separate focused commits. No production cutover follows automatically.

### Task 6: Recovery, capacity and release documentation

**Files:** Use/extend `scripts/staging_backup.py`; update `docs/operations/{deployment,backend-release-plan,local-development}.md`, `docs/migration/ROADMAP.md`, `apps/dashboard/README.md`, and `docs/product/platform-resolution-checklist.md`.

**Interfaces:** A release record identifies exact artifacts, configuration, owners, acceptance results and unresolved gates; source completion and production verification are separate statuses.

- [ ] Reconcile stale documentation against current code and Task 5 evidence; preserve historical entries as explicitly dated history.
- [ ] Obtain named recovery owners and agreed RPO/RTO, retention and expected traffic/photo volume before claiming operational readiness.
- [ ] Rehearse encrypted backup/isolated restore of app DB, identity DB/configuration and objects; reconcile revisions, counts/checksums, mappings, media access and measured recovery time.
- [ ] Measure representative reads, photo uploads and simulation concurrency; test dependency failure and recovery. Use approved traffic/latency/error targets, recording actual results and resource limits.
- [ ] Configure and exercise redacted logging, request IDs, dependency/error/latency/storage alerts and incident ownership.
- [ ] Rehearse cutover/rollback including preservation of writes made after cutover. Record exact rollback triggers and compatible prior artifacts.

### Task 7: Production routing and client release

**Files:** Review `apps/dashboard/vercel.json`, backend production deployment configuration, Android release configuration, `apps/dashboard/src/releases/current.json`, and existing release procedures.

**Dependencies:** Tasks 1–6 accepted; approved production domains/access/secrets; authorized private legacy export if migrating private history; release owner approval.

- [ ] Prepare the exact successor API proxy configuration only after the real production origin is assigned. Verify TLS, callback URLs, Set-Cookie, CSRF Origin checks, no caching of private responses and auth/media links under the same-origin route.
- [ ] Deploy reviewed immutable backend artifacts and run explicit migrations; require readiness and identity/storage acceptance before switching clients.
- [ ] Reconcile authorized migration data and access controls; freeze legacy writes only under the rehearsed cutover procedure.
- [ ] Build a new Android version with the existing signing identity and higher versionCode. Test physical-device fresh install, legacy upgrade, OIDC callback, expired session, offline retry and photo submission in staging.
- [ ] Obtain release approval for the concrete artifacts/configuration/evidence, then publish and verify public routes, signed APK checksum, identity and monitoring. Do not submit fabricated production observations.
- [ ] Observe the agreed acceptance window, retain rollback artifacts and reconcile new writes before retiring legacy paths.

## Completion criteria

Interface batch: truthful summaries/actions; usable error recovery, keyboard/mobile station selection; green repository checks; current visual review recorded or explicitly open.

Shared platform release: staging acceptance, production integration, migration, physical-device release, restore/capacity/alerts and rollback evidence accepted by named owners. Scientific decision use stays prohibited unless separately validated and authorized.

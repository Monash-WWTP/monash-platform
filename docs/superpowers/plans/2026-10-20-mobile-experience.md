# CitizenFlood mobile experience implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the approved map-first citizen app, coherent reporting/history, and branded account journeys on the connected Samsung.

**Architecture:** Keep Flutter native navigation and existing API/OIDC authorization. Isolate native map rendering from location/selection state; use a typed report draft across form/review/sign-in. Identity branding and email configuration form a separately testable delivery unit, with no cloud cutover.

**Tech Stack:** Flutter/Dart, Material3, MapLibre Native Flutter binding, FastAPI, authentik2026.8.3, existing green/logo assets.

**Spec:** `docs/superpowers/specs/2026-10-20-mobile-experience.md` (owner approved).

## Global constraints

- Destinations in order: Map, My reports, Account. Map opens first; Report here is its primary action.
- Citizens only; operators remain in dashboard. Anonymous map exploration remains available.
- Existing category wire values, units, API authorization, idempotency, secure token storage and privacy projections are preserved.
- Current location or explicitly chosen free point; selecting an existing report is a separate interaction.
- Preserve existing green identity and owned logo. No new institutional/measurement claims or invented condition criteria.
- Native48dp targets, screen-reader selected states, keyboard/system insets and Samsung Back support.
- API/domain/storage secrets stay server-side. Keep external-browser OIDC/PKCE and server MFA; no custom native password handler.
- Production provisioning, Vercel API rerouting, signed public release and scientific acceptance remain outside this plan.
- Existing local verification-email fix is uncommitted and must be retained; existing unrelated main-checkout files stay untouched.

## Review focus

1. Sign-in may finish after logout/navigation; stale results must not restore private state (Tasks2/6).
2. Map movement, overlapping markers and approximate public coordinates must not silently select a report location (Task3).
3. A submit timeout may follow a successful server commit; retry must not duplicate media/report (Task4).
4. An email can be opened in another browser or after expiration; confirmation must not masquerade as reset, and errors must be recoverable (Task1).
5. Large text, keyboard and permission denial can hide the primary action on a small Samsung screen (Tasks3/4/6).

## Task1 — Correct and brand identity journeys (independent delivery unit)

**Files:** modify `infra/staging/identity/bootstrap.py`, `infra/staging/compose.yaml`; create `infra/staging/identity/branding.css`, branded email templates under `infra/staging/identity/templates/email/`, `tests/test_identity_branding.py`; retain `tests/test_identity_email_templates.py`.

**Interfaces:** consumes approved logo `apps/citizenflood/assets/icon/icon.png` and existing authentik Flow/Brand/EmailStage models; produces deterministic idempotent local brand/template configuration. Export production setup instructions without deploying it.

- [ ] Diagnose the stalled phone flow using sanitized browser/identity/API timestamps: flow execution, callback, token exchange and account load. Reproduce the failing boundary before modifying configuration. Never capture bearer/verification tokens in review artifacts.
- [ ] Verify installed authentik Brand fields, template loader locations and supported CSS variables from its actual version/official docs. Use existing assets, readable light green/white account layout, concise product titles and shared favicon. Mount resources read-only to both server/worker where required. Do not reuse a stage's generic default reset template for enrollment.
- [ ] Run existing email test RED evidence (already observed missing template), then GREEN: enrollment=`email/account_confirmation.html` or its branded derivative, recovery=`email/password_reset.html` or its branded derivative; only enrollment activates the account. Add rendering assertions: confirmation mail has Confirm/Verify action and no Reset Password; recovery does the inverse, links use the supplied synthetic URL and templates escape user content.
- [ ] Apply scoped configuration updates transactionally/idempotently, without replacing passwords, signing keys, accounts or policies. Add configuration tests for matching brand/logo and separate flow titles/templates. Verify repeat bootstrap does not accumulate duplicate bindings.
- [ ] Test live enrollment/verification, expired/used link, recovery and canceled/repeated mobile sign-in; preserve original PKCE return and recovery revocation. If a real user must type credentials, pause only that operation and continue independent work. Record actual success or pending evidence; do not infer from token issuance alone.
- [ ] Run `uv run --locked pytest -q tests/test_identity_email_templates.py tests/test_identity_branding.py`; commit the identity unit separately after checks.

## Task2 — Owner history and identity-aware data seams

**Files:** modify `apps/citizenflood/lib/services/report_repository.dart`, `lib/models/report.dart`; create `lib/screens/my_reports_screen.dart`, `lib/widgets/report_detail_sheet.dart`, `test/widgets/my_reports_test.dart`; create `test/services/report_repository_test.dart`.

**Interfaces:** add `ReportRepository.own({int limit=25, int offset=0}) -> Future<ReportPage>` and `ReportPage(items: List<Report>, total: int, offset: int, limit: int)`. Reuse the existing owner endpoint; never derive My reports by filtering the mixed public list. Shared `ReportDetailSheet(report: Report, ownerView: bool)` explicitly controls private-media rendering.

- [ ] RED: My reports requests only `/api/v1/reports`, paginates25, displays Pending/Approved/Rejected, shows sign-in state when anonymous and clears rows/photos when identity changes mid-request. Test out-of-order completion after logout/account switch.
- [ ] Implement bounded owner pagination, refresh/empty/error/retry states and owner detail. Preserve observation time/category/value/unit and existing privacy boundaries. Check whether review reason is available in owner contract; if absent, add only an explicit owner-allowlisted review-reason field with API projection test/OpenAPI regeneration. Never expose reviewer/private audit data through public observations.
- [ ] GREEN: run repository/widget tests and existing `test/widgets/map_privacy_test.dart`; commit.

## Task3 — Native map, point selection and app navigation

**Files:** modify `pubspec.yaml`, `pubspec.lock`, `lib/screens/map_screen.dart`, `lib/screens/home_shell.dart`; create `lib/maps/map_selection.dart`, `lib/maps/citizen_map.dart`, `lib/screens/location_picker_screen.dart`, `test/maps/map_selection_test.dart`, `test/widgets/home_navigation_test.dart`.

**Interfaces:** `SelectedLocation(latitude: double, longitude: double, accuracyM: double?, source: LocationSource)` with `LocationSource.current/selected`; `LocationPickerScreen(initialLocation: SelectedLocation?)` returns `SelectedLocation?` through Navigator; `CitizenMap` adapts native controller events into location/observation selection. Widget tests inject a fake map adapter; device tests exercise real native rendering.

- [ ] Review maintained MapLibre Flutter binding compatibility against Flutter3.44.7/Dart3.12 and Android SDK/Gradle requirements. Pin the tested package in lockfile; use dashboard's `https://tiles.openfreemap.org/styles/liberty`, respect provider attribution and verify resource reachability. Remove raster-map dependency only after all references migrate.
- [ ] RED: initial destination Map; bottom labels Map/My reports/Account; tapping marker changes selected ID and opens matching detail without mutating report location. Overlap selection offers choices; logout clears private features, selected detail and camera. Location-picker cancellation retains prior draft location.
- [ ] Implement2D native map, branded compact app bar, recenter, accessible legend/controls, selected marker treatment and detail sheet. Show distinct device/accuracy location. Keep approximate public points distinguished from precise owner points. Implement loading/tile failure/offline/retry independently of observation data loading.
- [ ] Add centre-pin picker and Use current location. Permission denied/disabled/GPS timeout produce actions rather than implicit0,0; keep coordinates available as fallback when place names are unavailable. Confirm location returns an explicit value; Report here begins the report for that location. Native back cancels without submitting.
- [ ] GREEN: map state/navigation/privacy tests; smoke native style/markers/camera on Samsung before proceeding. Commit.

## Task4 — Draft, input, review and idempotent submission

**Files:** modify `lib/screens/category_screen.dart`, `lib/widgets/category_tile.dart`, `lib/screens/report_form_screen.dart`; create `lib/models/report_draft.dart`, `lib/screens/report_review_screen.dart`; extend `test/widgets/report_submission_test.dart`; create `test/widgets/report_review_test.dart`.

**Interfaces:** immutable `ReportDraft` holds selected location, category, nullable numeric value/condition, observedAt, note and optional local photo. `ReportReviewScreen(draft: ReportDraft)` returns to Edit without dropping fields; submission uses one validated snapshot and existing retry identity/media/key. Explicit condition is required, without changing wire enum.

- [ ] RED: category/location stay visible; numeric inputs show existing units; wastewater cannot advance without a condition; Review performs no network write. Edit preserves fields/photo/location/time; canceled sign-in preserves draft; large text/keyboard leaves Review reachable.
- [ ] Implement compact branded category choices and structured form using Material controls; location state visible, optional photo/note accessible, permission errors recoverable. No oversized generic tiles or lengthy guidance. Retain required input validation and explicit selected state.
- [ ] Implement Review summary/Edit/Submit and success Pending review with View my report. Ensure repository returns the created report ID (currently submit returns void); parse existing create response, retaining idempotent retries, and test first/uncertain/repeated response contracts.
- [ ] RED→GREEN for server-committed timeout then retry: same idempotency key/media/input, one record; editing after failed attempt starts a new payload identity. Upload failure preserves local photo. Existing session-generation fencing must still reject stale authentication completion.
- [ ] Run `flutter test test/widgets/report_submission_test.dart test/widgets/report_review_test.dart test/services/account_session_test.dart`; commit.

## Task5 — Account layout and coherent visual system

**Files:** modify `lib/screens/profile_screen.dart`, `lib/theme/app_theme.dart`, `lib/screens/home_shell.dart`; create `lib/widgets/account_status.dart`, `test/widgets/account_screen_test.dart`; include approved logo as runtime asset in `pubspec.yaml`.

**Interfaces:** Account screen consumes existing AccountSession and a cached/injectable account loader. Distinguish loading, canceled, expired, unverified and unavailable states; no new capability assignment surface.

- [ ] RED: anonymous account offers Sign in/Create account; signed-in shows identity/verification and Sign out; account fetch failure is actionable and never stays Loading account forever; a rebuild does not repeatedly refetch. Double tap does not launch concurrent auth. Anonymous map remains usable.
- [ ] Implement shared semantic colors/type/spacing and native components across screens; keep current green/logo, white backgrounds and clear selected/status text. Avoid decorative avatar dominating the account task. Product information is secondary. Create account launches approved enrollment through authentik and preserves return context; no native password handling.
- [ ] GREEN: account/session/widget tests; check48dp targets, TalkBack labels, text scaling and system insets. Commit.

## Task6 — Integration, Samsung acceptance and delivery

**Files:** update `apps/citizenflood/README.md`, `docs/operations/toolchains.md`, `docs/operations/platform-administration.md` only where behaviour changes; create `docs/operations/samsung-mobile-acceptance-2026-10-20.md`; update spec/plan progress and current gallery only after actual acceptance.

- [ ] Verify feature work isolation from current merged branch before execution; preserve existing uncommitted email fix/audit/spec/plan. Start feature branch at current merged main without copying secret files into Git.
- [ ] Run full Flutter tests/analyzer and staging debug build using checked-in public staging config. Run repository checks; if API projection changes, guarded disposable API suite plus OpenAPI snapshot checks. Existing local staging database is not the disposable test database.
- [ ] Install debug staging APK on SM-A076B via USB; preserve public APK/signing identity. Use `adb reverse tcp:8181 tcp:8181` and `adb reverse tcp:9100 tcp:9100`; local services remain loopback only. Verify full registration/login/verification/callback, report/create/review/photo/upload, uncertain retry, My reports and local admin moderation. Use clearly marked test observations; never publish precise private fixture locations.
- [ ] Batched physical UI/accessibility check: portrait/landscape, large text, keyboard, Back, TalkBack selected states, denied camera/location, offline, background/resume, overlapping marker details and logout/account-switch privacy. Inspect screenshots once, fix material defects as one batch, confirm once. Distinguish debug timing from profile-mode timings; report measured stages instead of promising a speedup.
- [ ] Independent whole-branch security/contract/UX review; reproduce substantive findings RED→GREEN, rerun affected suites. Verify migration/schema if touched. Commit acceptance evidence with pending items stated explicitly.
- [ ] Create/link PR(s), verify CI and authorized squash merge. Keep identity and app commits reviewable separately. Do not change Vercel backend routing, deploy production, replace public APK or claim scientific acceptance.

## Plan self-review

Approved spec sections map to Tasks1–6. Data interfaces use existing API boundaries; any review-reason addition is owner-only. The five review-focus failure classes have explicit tests in their owning tasks. Native rendering and browser email/callback behaviour have device/environment checks in addition to isolated widget tests. Cloud and public-release gates remain separate. Existing unresolved authentik loading is a required diagnostic, not a claimed fix.

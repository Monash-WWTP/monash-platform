# Citizen Observation Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task in the current isolated worktree. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace ambiguous new citizen reports with directly observable events and context-qualified optional measurements, while preserving legacy records.

**Architecture:** Keep existing v1 routes and stored payloads. Introduce a protocol-versioned v2 observation API, validated discriminated payloads and explicit client capability discovery. Reuse report ownership, media, moderation, idempotency and privacy infrastructure; no automatic lab/scenario conversion.

**Tech Stack:** FastAPI/Pydantic/SQLAlchemy, Flutter/Dart/Material/MapLibre, React/TypeScript, existing PostgreSQL and local staging.

**Spec:** docs/superpowers/specs/2026-10-21-citizen-observation-protocol.md (approved21October2026).

## Global constraints

- Citizens report what they directly observe; observations are not diagnoses, official warnings, plant-performance scores or safe-route guarantees.
- Unknown, not observed, trace, missing and zero are distinct states.
- Existing v1 records remain readable without assigning a missing interval, datum, subject or method retrospectively.
- Numeric values require their specified method/context; no invented environmental alert cutoffs.
- Owner identity, notes, media and exact locations stay private; public output stays allowlisted and rounded.
- Software tests do not establish scientific validation. Field pilot and reference-based validation remain separate.
- Preserve existing green branding, compact map-first layout, short labels, review flow and native accessibility.
- API deploy/capability acceptance precedes new-client submission. No production provisioning or public APK release in this plan.

## Review focus

- Old clients encountering new categories must not crash or silently reinterpret them.
- Trace/unknown/not-observed must survive create, review, read and export without becoming zero/normal.
- Rain interval timezone/order and stage datum identity must prevent incomparable readings masquerading as the same metric.
- Changed account/logout or uncertain media/write results must preserve privacy and retry identity.
- Numeric measurement mode must not encourage unsafe sampling or imply a validated diagnostic threshold.

## Task1 — Versioned domain contract and compatibility

Files: create services/api/app/reporting/observations.py; modify services/api/app/http/contracts.py and services/api/app/routers/reports.py; tests services/api/tests/test_observations.py; existing schemas.py remains v1.

Interfaces: discriminated ObservationV2Input with protocol_id='citizen-observation', protocol_revision=1, observation_type, observed_at, location/source/accuracy and optional private note/media. Types: flooding, rain_occurrence, water_appearance, rainfall_accumulation, water_reading, temperature. Explicit categorical/unknown values; per-type context models. Numeric modes separate measured/estimated, depth/stage, air/water and require the approved context. Station/datum reference is a controlled identity/revision, not a free claim of certified reference quality.

- [ ] Write failing tests for required context; unknown/zero/trace distinctions; finite values; ordered timezone-aware rainfall interval; signed referenced stage versus nonnegative depth; temperature subject; no conflicting numeric/categorical fields.
- [ ] Run targeted tests and observe meaningful failures.
- [ ] Implement context models, validators and protocol registry. Retain unmodified v1 contract tests.
- [ ] Define /api/v2/observation-protocols capability response and /api/v2/observations create/owner history/detail. Persist versioned payload using existing CitizenReport ownership/idempotency/media checks; category identifies new observation type, while v1 queries explicitly exclude v2 records. No historical payload rewrite.
- [ ] Test same-key/different-payload conflict, retries, owner fencing, media ownership, timestamp handling and old-client compatibility. Determine from database constraints whether a migration is required; add one only if actual columns/constraints change.
- [ ] Run API tests, regenerate OpenAPI, commit independently testable backend.

## Task2 — Public projection and operator review

Files: reports.py or focused observation router; http/contracts.py; apps/dashboard/src/api/monitoring-types.ts and pages/ModerationPage.tsx; source API/React tests.

- [ ] RED: v1 community/moderation responses cannot contain unknown v2 categories; v2 mixed history clearly identifies protocol/legacy origin. Public v2 projection excludes owner identity, note, media path and precise coordinates/reference data.
- [ ] Implement explicit v2 projections and v2 moderation reads, retaining existing publication workflow and reason audit. Publication approval never sets scientific validation status.
- [ ] Update dashboard type guards/rendering to show event/category or value with required context and legacy labels. Preserve historical Normal/Warning/Critical as subjective legacy reports.
- [ ] GREEN: privacy, permission, pagination and mixed-version display tests; regenerate OpenAPI; commit.

## Task3 — Flutter domain/repository and capability gate

Files: create lib/models/observation.dart and observation_draft.dart, services/observation_repository.dart; adapt report.dart/report_repository.dart only where needed for legacy views; tests/models and tests/services.

- [ ] RED: parse every v2 type and unknown state, reject invalid context without losing original v1 meaning; no submissions to unsupported backend.
- [ ] Implement immutable typed draft and serialization matching API; fetch supported protocol revisions before enabling new submission. Show an actionable service-unavailable state rather than silently send old ambiguous fields.
- [ ] Merge compatible v1/v2 owner/map reads with explicit kind/version and owner/public presentation; preserve generation fencing and safe media/idempotency behavior.
- [ ] GREEN: payload/roundtrip/capability and mixed-version tests; commit.

## Task4 — Citizen event flow and optional measurement forms

Files: lib/widgets/report_menu.dart, screens/map_screen.dart; create observation_form_screen.dart, observation_review_screen.dart and focused measurement_fields.dart; adapt shared detail/list/history rendering.

- [ ] RED: main menu has Flooding, Rain, Water appearance, with an Add measurement path; no silent normal/zero/default choice. Location/time retained across category choice and editing.
- [ ] Implement short event questions and explicit unknown/not-observed choices. Appearance fields describe visible features with other/unknown; do not label a plant healthy/failing or identify a pollutant/cause. Require an affirmative response/unknown rather than treating an empty checklist as normal.
- [ ] Implement optional instrument forms: rainfall amount/trace and start/end/gauge; water depth with surface reference or stage with registered datum; air/water temperature with instrument and sample context. Unknown calibration/precision remains explicit. No unsafe field measurement prompts.
- [ ] Review shows actual event/measurement, location/source, observed time, method/context, optional private evidence and publication state. Preserve submit locking, retry keys, media reuse, Edit and Back behavior.
- [ ] GREEN: form validation, unknown semantics, keyboard/Back, narrow/large text, accessible labels and existing reporting regressions; commit.

## Task5 — Local integration, documentation and field-validation boundary

Files: docs/operations/mobile-ux-checklist.md, samsung-mobile-acceptance-2026-10-20.md, docs/science/CITIZEN_OBSERVATION_METRICS_REVIEW.md, API snapshot, app README; public manual update only after verified behavior.

- [ ] Run complete Flutter/analyzer/build, guarded disposable API suite, dashboard checks, repository/import inventory and OpenAPI checks.
- [ ] Rebuild local API then staging APK; confirm protocol capability before installing client. Keep v1 APK/routes operational for existing clients.
- [ ] On Samsung, test one categorical event/unknown and representative measurement form; sign-in, media/review/submit/history; mixed legacy records; denied permissions, offline/retry, account switch, TalkBack, large text, portrait/landscape and keyboard. Use marked synthetic records and leave them unpublished.
- [ ] Document actual results and unresolved gates. Prepare a separate field-pilot checklist using paired references, independent observers, held-out sites/times, error/agreement and sampling-bias analysis. No arbitrary accuracy acceptance cutoff or academic-validation claim.
- [ ] Review compatibility/privacy/scientific semantics once, resolve substantive findings, verify CI and update linked PR(s). No production cutover/public signed APK replacement.

## Self-review and execution

Each new observation type maps to context validation, serialization, UI and privacy tests. Old and new clients coexist through separate routes and explicit v1 filtering. A shared domain contract changes before client activation. The current approved design establishes data meaning; it does not authorize unsupported thresholds or claim field validation. Execute inline after this written plan is reviewed.

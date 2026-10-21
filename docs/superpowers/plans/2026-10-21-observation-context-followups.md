# Observation context and follow-ups implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add obtainable condition/evidence context and linked flooding updates to the existing CitizenFlood and operator platform.

**Architecture:** Extend the existing `/api/v2` observation service with protocol revision2 while retaining revision1. Reuse CitizenReport JSON, ownership, media, moderation, immutable review and mobile navigation. No separate survey, database, lab-data conversion or simulation integration.

**Tech Stack:** FastAPI/Pydantic/PostgreSQL, Flutter/MapLibre, React/TypeScript.

**Spec:** docs/superpowers/specs/2026-10-21-observation-context-followups.md (approved21October2026).

## Global constraints

- Revision1 and historical records remain readable with their original meaning; no invented backfill.
- Missing and Unsure remain distinct. User-entered observations are not certified measurements.
- Reuse the compact green map-first flow; optional context stays progressively disclosed.
- Owner/reviewer context remains private; public coordinates remain rounded.
- No external weather provider, production provisioning or public signed APK replacement.
- Citizen observations remain separate from laboratory measurements and simulation inputs.

## Review focus

- An older client must not submit revision1 while silently losing revision2 context.
- Removing/replacing a photo must clear the old source, including after failed upload/retry.
- A follow-up must not disclose another user's report or inherit private state after account change.
- Reused locations must not inherit GPS accuracy; changing location must invalidate comparison.
- Unknown/absent flooding must not retain a directional change or movement from an earlier selection.

## Task1 — Versioned server contract

Files: `services/api/app/reporting/observations.py`, `services/api/app/routers/observations.py`, `services/api/tests/test_observations.py`, `services/api/openapi.json`.

Interfaces: retain revision1 models; add a revision2 input/view with optional `photo_source: camera|gallery`, optional `previous_observation_id`, optional `level_change: higher|same|lower|unknown`, and flooding-only optional `movement: still|flowing|unknown`. Capability response retains its existing revision1 keys and adds `supported_revisions: [1,2]`. New fields are forbidden on revision1. Response/public schemas accept both revisions and report each record's stored revision rather than the current server constant.

- [x] Write `test_revision_two_context_validation`: revision1 remains valid; revision1 extras fail; movement requires present flooding; directional comparison requires present flooding and a previous ID; explicit unknown is distinct from omission; photo_source requires media_id and vice versa for revision2.
- [x] Run targeted tests against guarded disposable DB5433; observe missing revision2 support fail.
- [x] Implement revision-discriminated input/view models and allowlisted public movement only. Preserve revision1 serialization/idempotency hashes without inserting new null defaults into old payloads.
- [x] Write `test_followup_ownership_time_location`: earlier own flooding report accepted; foreign/missing/incompatible report returns nondisclosing404; later/equal observation time rejected; coordinates must exactly match prior selected point and source selected with no GPS accuracy; reject comparisons without a link. A link without directional comparison permits unsure/absence.
- [x] Implement `validate_followup(db, account_id, body) -> None` in the observation router before persistence, after existing idempotency reconciliation. Store immutable linkage in report JSON. Return private links only to authorized owner/reviewer; no public linkage/photo source.
- [x] Run full API suite, regenerate OpenAPI with explicit test configuration; commit backend independently.

## Task2 — Mobile context and evidence lifecycle

Files: `apps/citizenflood/lib/models/observation.dart`, `lib/services/observation_repository.dart`, `lib/screens/observation_form_screen.dart`; tests `test/models_observation_test.dart`, `test/services/observation_repository_test.dart`, `test/widgets/observation_form_test.dart` (all relative to apps/citizenflood).

Interfaces: discovery exposes supported revisions; form selects revision2 only when advertised and otherwise retains revision1 ordinary collection. Follow-up requires revision2 and shows unavailable/retry on older service. Immutable ObservationDraft retains new fields; review/detail context displays source and change labels.

- [x] Write tests for revision capability negotiation, movement missing/unknown, review roundtrip and camera/gallery/remove/replace provenance. Verify revision1 ordinary submissions contain no revision2 fields.
- [x] Observe failures, then implement optional Still/Flowing/Unsure chips only for observed flooding; clear movement on other responses. Record photo source from the existing picker action; clear on removal/replacement and retain source consistently with reused upload media.
- [x] Preserve existing editable observation time and location metadata; add no extra permission or EXIF inference. Test selected-location change removes GPS accuracy.
- [x] Verify immutable review, edit-after-uncertain retry identity and account-change clearing cover the additional context. Run Flutter tests/analyzer; commit.

## Task3 — Linked updates in existing report navigation

Files: `apps/citizenflood/lib/widgets/report_detail_sheet.dart`, `lib/screens/map_screen.dart`, `lib/screens/my_reports_screen.dart`, `lib/screens/observation_form_screen.dart`; create `apps/citizenflood/test/widgets/observation_followup_test.dart`.

Interfaces: add an optional owned-flooding update action to the shared report detail route. ObservationFormScreen accepts an optional original Report; starts a fresh draft at that selected point and current editable time, with original ID and no copied answers/evidence/GPS accuracy. Current repository resolves owner identity before enabling the action.

- [x] Write failing tests: only own compatible flooding has Report an update; original remains unchanged; fresh time/no copied media; Higher/Same/Lower/Unsure reviewed with reference; changing location clears link/comparison; unknown/absence clears movement/directional comparison; logout closes flow.
- [x] Implement action through shared navigation from map/list/My reports; show comparison only in the update flow. A changed location becomes an ordinary new observation after clearing linkage and comparison, explicitly reflected on review.
- [x] Submit through existing locked idempotent flow; successful update opens current My reports tab and refreshes without duplicate navigation. Run full Flutter tests, analyzer and debug build; commit.

## Task4 — Operator context, integration evidence and delivery

Files: `apps/dashboard/src/api/observations.ts`, `apps/dashboard/src/pages/ModerationPage.tsx`, `apps/dashboard/tests/observation-protocol.test.ts`, `docs/operations/citizen-observation-protocol.md`, `docs/operations/mobile-ux-checklist.md`, `docs/operations/samsung-mobile-acceptance-2026-10-20.md`, `apps/citizenflood/README.md`.

- [ ] Write failing summary tests for movement and private update/source context. Implement owner/reviewer context rendering in existing moderation cards without public identifiers; retain revision labels and publication-is-not-validation distinction.
- [ ] Run dashboard tests/build, full guarded Python tests, Flutter tests/analyzer/build, repository and pinned inventory checks; inspect outputs and diff for secrets.
- [ ] Rebuild local API image, verify revisions1/2 capability, install staging debug APK. On unlocked Samsung submit a synthetic flooding original/update pair, inspect optional context and mixed history; leave unpublished. Record unavailable device checks accurately rather than marking them passed.
- [ ] Perform one final whole-change review, reproduce/fix substantive defects with regression tests, update operational docs with actual verification and remaining field/production gates.
- [ ] Commit/push to existing PR11; update scope/evidence, verify CI through T3 notifications when watching, and hand back with accurate limits. Do not merge or publish based solely on software tests.

## Self-review

All spec sections map to Tasks1–4. Shared field names and enum values are fixed above; revision1 fallback never receives new context. Follow-up privacy, time ordering and location matching have server tests and lifecycle tests. Photo provenance is a picker-origin claim, not authenticity. No external data integration is silently added. Execution remains inline in this session after plan review.

## Execution evidence

201 Python tests pass/1skip,53 Flutter tests pass,46 dashboard tests pass, analyzer clean, builds pass. OpenAPI regenerated; repository/pinned inventory pass. Local API revision2 advertised and debug APK installed. One fresh whole-change review found no concrete defects. Samsung locked at physical acceptance; original/update device submission remains pending. Operator workflow design approved separately and plan prepared; no operator-response code included in this extension.

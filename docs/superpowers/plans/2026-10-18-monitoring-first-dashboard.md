# Monitoring-first Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make monitoring the primary experience and provide a clearly separated research sandbox with trustworthy run comparison.

**Architecture:** Retain the existing monitoring and plant workspace routes. Improve observation presentation without manufacturing plant status; isolate research provenance and comparison calculations in small modules. Enforce comparison compatibility on the API as well as in the interface.

**Tech Stack:** React, TypeScript, Zustand, TanStack Query, ECharts, FastAPI, SQLAlchemy, pytest.

**Spec:** `docs/design/scenario-workspace-proposal.md`

## Global Constraints

- Keep the approved green/charcoal/white palette, Manrope and shared operator controls.
- Do not put simulation controls or model outputs on the monitoring overview.
- The 3D twin remains removed. Keep measured observations distinct from simulated values.
- No operational health score, real-time status, causal ranking or decision-use claim may be inferred from the current data/model.
- Preserve legacy source/data bytes and scientific equations; this work does not validate the model.
- Read CONTRIBUTING.md, docs/migration/ROADMAP.md and docs/science/VALIDATION.md before implementation.

## Review Focus

- An observation without a timestamp or quantifiable reading stays explicitly unavailable, never zero or current (Task 1).
- A sampling location without a matching plant must not open another plant’s research workspace (Task 1).
- A failed latest run cannot enter comparison; changing plants clears selected runs and reference (Tasks 2–3).
- Reordered or malformed time series cannot silently pair values with the wrong run/date (Tasks 2–3).
- Zero/missing reference metrics and changed accounting factors cannot imply a quantified process benefit (Task 3).

---

### Task 1: Monitoring hierarchy and secondary research entry

**Files:** Modify `apps/dashboard/src/pages/MapPage.tsx`, `apps/dashboard/src/components/monitoring/StationDashboard.tsx`, `apps/dashboard/src/components/OperatorHeader.tsx`; create `apps/dashboard/tests/monitoringJourney.test.ts`.

**Interfaces:** Consume existing plant, station and laboratory APIs. Preserve existing route `/dashboard/plants/:plantId`; label its entry “Research sandbox”. No automatic monitoring-to-model input transfer.

- [x] Add rendering tests asserting latest available observation date/source, explicit unavailable/BDL states, monitoring navigation, and secondary research action only for a matched plant. Cover unsorted observations and missing dates without claiming freshness.
- [x] Run `npm test` in `apps/dashboard`; confirm the new assertions fail before implementation.
- [x] Put observation history, units, coverage and source ahead of research access. Retain search/list, accessible map fallback, station/plant distinction and modal focus behavior. Use explicit timestamps rather than arbitrary fresh/stale thresholds.
- [x] Run `npm test` and `npm run lint`; commit the monitoring deliverable.

### Task 2: Server-enforced comparison compatibility

**Files:** Modify `services/api/app/routers/simulations.py`; create `services/api/app/services/comparison.py` and `services/api/tests/test_comparison.py`; regenerate the repository OpenAPI snapshot only if the public schema changes.

**Interfaces:** Add `validate_comparison(runs: list[SimulationRun]) -> None`, raising structured `ApiError` for incompatibility. Preserve CompareRequest and CompareOut shapes, request ordering and existing missing-run 404 behavior.

- [x] Add API tests for 2–4 unique completed runs, duplicate IDs, failed/running runs, cross-plant runs, model ID/version/artifact mismatches, empty/different date vectors, series-length mismatches and incompatible metric sets. Assert invalid comparisons return 422 with a useful stable error code; valid runs retain request order and run_id pairing.
- [x] Run the new test module against the exact disposable test database; confirm failures.
- [x] Implement validation before serializing results. Compare model identity/version/artifact and actual date vectors; require nonempty equal metric sets with every series matching its dates. Units follow the shared model/metric contract; no silent interpolation or index alignment. Accounting factor/threshold differences remain visible input differences rather than being discarded.
- [x] Run comparison, contract, provenance and OpenAPI tests; commit the API safeguard.

### Task 3: Explicit reference, immutable differences and result deltas

**Files:** Modify `apps/dashboard/src/api/types.ts`, `apps/dashboard/src/api/hooks.ts`, `apps/dashboard/src/components/comparison/ComparisonView.tsx`, `apps/dashboard/src/stores/scenarioStore.ts`, `apps/dashboard/src/pages/WorkspacePage.tsx`; create `apps/dashboard/src/components/comparison/comparisonModel.ts`, `apps/dashboard/tests/comparisonModel.test.ts`, `apps/dashboard/tests/workspaceState.test.ts`.

**Interfaces:** Extend Run to include existing backend input_snapshot/artifact_digest/error_code/parent_run_id fields. Add `metricDifference(value: number | null, reference: number | null, percentagePoints: boolean): { absolute: number | null; relativePct: number | null }`. Add `changedInputs(reference: Record<string, unknown>, candidate: Record<string, unknown>): Array<{ path: string; reference: unknown; candidate: unknown }>` using deterministic object-key traversal and atomic array values. Add store `resetWorkspace(): void` clearing draft, active run, comparison, reference and view.

- [x] Test numeric zero, missing/nonfinite values, zero reference (no relative percentage), screening percentage-point changes, deterministic nested input differences and unchanged snapshots. Test plant reset and reference removal when its selected run is removed.
- [x] Run frontend tests and confirm failures.
- [x] Resolve each candidate’s actual run status; permit completed runs only, label loading/failure and selection limit. Require an explicit selected reference. Render run IDs, model/version, artifact and dates, immutable input differences, then values and deltas. Highlight changed factors/thresholds and state that fixed-factor GHG cannot quantify aeration/maintenance benefit. Join time series by run_id and use validated dates. Add retry and incompatibility states; never retain stale results for a different selection.
- [x] Use resetWorkspace on plant changes; ensure no old-plant query/result is shown during transition. Run frontend tests, lint and build; commit comparison.

### Task 4: Research workflow, methods and end-to-end verification

**Files:** Modify `apps/dashboard/src/pages/WorkspacePage.tsx`, `apps/dashboard/src/components/scenario/ScenarioPanel.tsx`, `apps/dashboard/src/components/results/ResultsPanel.tsx`; create `apps/dashboard/src/components/research/MethodsPanel.tsx`; extend operator journey tests and update `docs/operations/staging-acceptance-2026-10-18.md`.

**Interfaces:** Keep existing scenario/run API contracts. MethodsPanel presents the checked-in science audit’s distinctions and primary source links; it does not claim model calibration. Results use immutable run inputs for maintenance annotations, rather than the current editable draft.

- [x] Add tests for research labelling, monitoring return link, configure/run/inspect/compare destinations, immutable run metadata, context-only weather/rainfall, methods/source access, failed run retry and no operational recommendation language.
- [x] Run tests to confirm new assertions fail, then implement the grouped workflow, units/default assumptions and concise methods panel. Preserve inputs on run failure and distinguish sourced GHG accounting from unvalidated effluent relationships.
- [x] Run frontend tests/lint/build and full Python tests using the guarded disposable DB. Run repository and manifest checks described in CONTRIBUTING.md. Record actual results and any skips.
- [x] Use T3 preview to check desktop and narrow screens: monitoring → details → research → run → inspect → compare, keyboard navigation, empty/missing/error states, selection reset and methods. Use synthetic fixtures, explicitly recording that they are not scientific validation or production acceptance.
- [x] Review the final diff for science claims, accessibility and contract regressions; fix findings, repeat affected checks, update acceptance notes and commit. Do not deploy or claim launch readiness while external release gates remain open.

Completed 2026-10-18. Final review fixes and remaining limitations are recorded in docs/operations/staging-acceptance-2026-10-18.md.

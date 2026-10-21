# Operator observation response implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for inline execution, task by task.

**Goal:** Turn citizen reports into accountable operator investigations without changing original observations or conflating publication with resolution.

**Architecture:** Add response state and append-only response events linked to existing CitizenReport IDs. Expose MFA-protected response APIs and an Operations reports dashboard route. Keep original report, moderation and scientific semantics intact.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic/PostgreSQL, React/TypeScript, existing browser sessions and dashboard UI.

**Spec:** docs/superpowers/specs/2026-10-21-operator-observation-response.md (approved21October2026).

## Global constraints

- No automatic equipment control, emergency dispatch, hazard severity, causal plant attribution or scientific-validation certification.
- Operational notes, assignees, inspection evidence and exact locations remain private.
- Original citizen records and publication status remain unchanged by response actions.
- All response reads/writes require report:respond and verified operator MFA; mutations retain browser CSRF protection.
- No new identity database, arbitrary SQL/shell, citizen messaging, live sensor integration or public release.

## Review focus

- Two operators acting on stale state must receive a conflict, never silently overwrite assignment or closure.
- Permission removal must fence subsequent reads/writes and assignment to ineligible accounts.
- A failed action must not leave an audit event without its matching state/history, or vice versa.
- Closing or reopening must preserve inspection/action history without implying publication or scientific validation.
- A historical legacy report must remain investigable without inventing its measurement context.

## Task1 — Response persistence and authorization

Files: `services/api/app/db/platform.py`; create Alembic migration after `e43b2c90ab01`; `services/api/app/identity/dependencies.py`, `services/api/app/admin_schemas.py`, existing admin user capability UI; create `services/api/tests/test_operator_response.py`.

Interfaces: `ReportResponse` keyed by report_id with revision (starts1 on first write), state (unassigned/assigned/investigating/closed), assignee_id nullable, plant_id/station_code nullable, updated_at. `ReportResponseEvent` immutable id/report_id/revision/actor_id/action/reason/details/created_at. Each accepted write increments revision exactly once; unique report_id/revision event constraint. Default virtual read state is revision0/unassigned before first action. Add `require_responder = capability('report:respond')` and the grant option to existing protected RoleChange/admin forms.

- [ ] Write failing tests for no-permission/no-MFA access and supported role grants, then add capability enforcement with existing session revocation/audit behavior.
- [ ] Add models/migration with report/account/plant/station foreign keys and unique event revision; no cascade deletion of report history. Verify upgrade/downgrade/upgrade and schema checks on disposable DB5433 only.
- [ ] Run identity/admin/migration tests and commit.

## Task2 — Atomic response service and APIs

Create `services/api/app/reporting/operator_response.py` (strict schemas), `services/api/app/services/operator_response.py` (transactions), `services/api/app/routers/operator_response.py`; modify `services/api/app/main.py`, reporting media authorization only if needed for responder evidence access; tests `services/api/tests/test_operator_response.py`, OpenAPI snapshot.

Interfaces under `/api/v1/operations`:
- GET `/reports?state=&offset=&limit=` bounded100, includes explicitly projected private legacy/versioned report and current response state; list is independent of publication status.
- GET `/reports/{id}` includes original report and ordered response events.
- GET `/responders` returns eligible account IDs/display labels only to responders.
- POST `/reports/{id}/events` body includes `expected_revision`, `action`, `reason`(3..1000 chars), and action-specific fields. Actions: acknowledge, assign, associate, inspect, act, close, reopen. All schemas forbid extras and nonfinite values.

Transitions: acknowledge moves unassigned/assigned to investigating; assign requires eligible assignee and sets assigned unless already investigating; associate validates existing plant/station and preserves state; inspect requires timezone-aware observed_at not future and result confirmed/not_confirmed/unable_to_verify plus method/evidence note, sets investigating; act requires action note and preserves active state; close requires disposition note plus prior inspection or action, sets closed; reopen requires closed and reason, sets investigating. Closed records reject other mutations until reopened. No deleting history or changing citizen payload. New state insert is serialized by locking CitizenReport first, then checking expected_revision; stale requests409. Events and AuditEvent commit in same transaction.

- [ ] Write `test_response_stale_atomic_history`: first write revision1, stale retry409, rejected mutation leaves state/event/audit counts unchanged; original payload/status unchanged after full lifecycle.
- [ ] Write `test_assignment_and_association_validation`: only eligible responder IDs accepted, nonexistent registry values rejected, permission-revoked assignee rejected.
- [ ] Write `test_inspection_closure_reopen`: required context/time, closed-state guards, close requires recorded inspection/action, reopening preserves full event sequence; legacy report accepted without altered semantics.
- [ ] Observe RED, implement schemas/services/router with explicit output models and private projections. Apply responder access to private photo reads only when authorized; add nondisclosure regressions.
- [ ] Run full guarded Python suite and export OpenAPI; commit.

## Task3 — Existing dashboard operations workflow

Create `apps/dashboard/src/api/operator-response.ts`, `apps/dashboard/src/pages/OperationsReportsPage.tsx`, focused components under `apps/dashboard/src/components/operations/`; modify actual route table in `apps/dashboard/src/main.tsx` or imported router and existing operator navigation. Tests create `apps/dashboard/tests/operator-response.test.ts` and UI integration coverage consistent with existing tooling.

Interfaces: typed response state/event DTOs matching Task2; existing fetchApi and useAccount enforce transport/session lifecycle. Display report kind, observed/submitted times, revision/legacy marker, location, context and private evidence link; current state/assignee and ordered timeline. Forms for each action use current expected_revision and required reason. Registry choices reuse protected existing APIs only if responder is allowed; otherwise provide dedicated responder-scoped registry projection in Task2 rather than granting admin.

- [ ] Write failing tests for labels/actions/state guards, stale409 recovery and payload fields; implement forms with existing green controls and accessible labels.
- [ ] Keep unsaved text after failed requests; on409 refetch state and require renewed action, never blindly replay. Disable writes while submitting; permissions loss clears private cached responses.
- [ ] Link Operations reports from operator navigation; keep moderation separately labeled as public-summary review. State clearly that inspection confirmation is not scientific certification; do not display invented priority/SLA.
- [ ] Run full dashboard tests/build and inspect desktop/mobile layouts and permission-denied/error states; commit.

## Task4 — Local acceptance, docs and delivery

Files: create `docs/operations/operator-response.md`; update administration guide, platform workflow links and acceptance record.

- [ ] Run full Python/dashboard suites, migration checks, OpenAPI/repository/pinned inventory checks. Rebuild local API and apply migration through staging workflow, never run destructive tests on local staging data.
- [ ] Use synthetic operator with explicit responder grant/MFA; verify assignment, inspection, action, closure/reopen, stale conflict and unchanged citizen publication status in local dashboard. Leave synthetic citizen reports unpublished.
- [ ] One fresh whole-change review, one regression-backed fix pass for substantive findings; document actual evidence and operational/team/production gates. No field accuracy or readiness claims from CI alone.
- [ ] Commit/push linked PR, update description and observe CI through T3 watcher when requested. No production provisioning or public APK replacement.

## Self-review

The approved workflow, permissions, immutable original records, separate publication/science semantics and local acceptance are all mapped to tasks. Transaction boundaries and concurrency are specified before UI work. Responder-scoped registry reads avoid accidental admin grants. Plant process monitoring, researcher export, scheduled sampling and sensor freshness remain separate systems with no fabricated availability.

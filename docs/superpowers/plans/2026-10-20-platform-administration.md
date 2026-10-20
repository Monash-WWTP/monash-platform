# Platform administration implementation plan

> Execute inline with test-first changes and independent review. The approved design is `docs/superpowers/specs/2026-10-20-platform-administration.md`.

**Goal:** Add secure routine administration to the existing green dashboard while preserving historical evidence and deployment boundaries.

**Architecture:** Add a protected FastAPI admin router and service layer, append-only per-plant configuration revisions through one Alembic migration, and a responsive dashboard admin workspace using existing controls. Reuse authentik for account lifecycle and existing report moderation. The first administrator is granted only by the trusted CLI.

**Constraints:** Every admin endpoint requires server-owned `platform:admin` and operator MFA. Browser writes retain CSRF. No password/secret editor, arbitrary command/SQL, hard deletion of historical data, self-granted administration, or science-validation toggle. Existing Vercel hosting stays. Server not provisioned: deployment remains pending.

## Task 1 — Permission boundary and account administration

Files: `services/api/app/identity/administration.py`, `identity/dependencies.py` (small admin dependency only), `routers/admin.py`, `services/admin.py`, `scripts/administer_account.py`, focused backend tests.

- Write failing anonymous/nonadmin/no-MFA/CSRF/account-list/privacy tests.
- Extend allowed capability vocabulary with `platform:admin`; CLI is the only way to grant/revoke this capability.
- Add protected paginated native-account search and updates to ordinary application capabilities. Preserve existing platform-admin capability on browser edits; require reason and expected current capabilities; refuse stale edits. Use current actor account in audit and revoke target browser sessions.
- Keep legacy identities out of normal role-grant flow. Do not claim capability removal disables the identity-provider account. Verify fail-closed permission and session revocation behavior.

## Task 2 — Versioned plant/station configuration

Files: `services/api/app/db/platform.py`, one new `services/api/alembic/versions/` migration, `services/admin.py`, `routers/admin.py`, admin schemas, simulation snapshot integration and focused tests.

- Write failing tests for invalid/nonfinite values, stale revisions, unique codes, canonical units and immutable historical run/configuration evidence.
- Add append-only `PlantConfigurationRevision` with plant/version uniqueness, actor, reason, canonical payload, source references/applicability notes and timestamp. Lock the plant row and check expected revision on writes; all changes and AuditEvent commit atomically.
- Add create/update plants and equipment; validate location/capacity/types/availability. Thresholds/factors require explicit units and user-supplied reference/applicability text; label provenance as supplied, not independently verified. Do not infer scientific acceptance.
- Add station metadata create/update with protected typed fields and stale-state guard. No browser editing/deletion of historical sample rows.
- Include resolved configuration revision and source metadata in immutable plant snapshots. Keep old records unchanged and make compatibility/input differences visible.
- Verify migration upgrade/downgrade/schema check and independent run replay/comparison regressions.

## Task 3 — History and operational status

Files: `routers/admin.py`, `services/admin.py`, tests.

- Add bounded audit-history pagination and read-only status: model/version/unvalidated policy, deployment environment and dependency readiness summary. Return sanitized statuses only; no endpoints/secrets/credentials or private report content.
- Reuse current moderation endpoint/UI rather than implementing duplicate queues. Verify every status/history path uses the same admin/MFA boundary.

## Task 4 — Dashboard workspace

Files: `apps/dashboard/src/pages/AdminPage.tsx`, `src/api/admin.ts`, existing route and operator navigation, focused UI/contract tests.

- Add `/dashboard/admin` with Users, Plants, Stations, History and Status views. Use existing green design tokens and native controls; no new UI framework.
- Use server capability gating, explicit form labels/units, required reason/source fields and Save actions. Keep inputs after failures; show field errors and conflict/reload guidance. Do not expose controls that grant platform administration or promise identity-provider actions.
- Link to existing report moderation and docs. Handle loading, empty, denied and error states. Verify at desktop/mobile widths and keyboard focus.

## Task 5 — Integration, documentation and delivery

- Regenerate OpenAPI and review additive client contracts.
- Run guarded disposable-DB API/simulation/repository suites; frontend tests/lint/build; migration/schema checks. Run independent security/contract review and fix findings.
- Update admin/bootstrap instructions and audit-remediation ledger; do not mark production/scientific/physical-device acceptance complete.
- Open PR, verify hosted CI and use the owner's standing squash-merge authorization after readiness. Production API cutover and latest public APK remain pending actual server provisioning and acceptance.

## Review focus

Account search must not leak private reports; grants cannot elevate the actor; edits must not overwrite intervening changes; old runs/revisions remain immutable; unknown source provenance must stay unknown; no status result may be interpreted as a successful restore/recovery/physical-device drill.

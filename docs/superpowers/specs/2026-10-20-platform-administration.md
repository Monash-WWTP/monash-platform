# Platform administration design

## Purpose and approved intent

The owner requested resolution of the full readiness checklist, including a general admin panel. Administrators should manage routine platform operations through the existing green dashboard, with authenticated backend enforcement and recorded changes. The panel complements the API/identity/database/storage services; it cannot replace them or establish scientific validation.

## First release scope

A protected `/dashboard/admin` workspace with Users, Plants, Stations, Configuration history and Service status views. Reuse existing report moderation rather than duplicate it. Registration/recovery remain in authentik; expose operator guidance and identity-admin navigation, not a second password database or a new invitation email system.

- Users: paginated/searchable native accounts; grant/revoke citizen/operator/reviewer capabilities with a required reason. Initial platform administrator is provisioned by the trusted server CLI. Administrator grants/revocations remain CLI-only for the first release; browser users cannot elevate themselves. Every change revokes affected browser sessions and records the acting account and before/after values. The UI does not claim a password reset or identity-provider disable occurred merely by changing application permissions.
- Plants: create/update plant identity, location, design capacity, equipment baseline availability and description. Validate finite coordinates, positive capacity, unique code, known equipment types and availability in [0,100]. Avoid hard deletion of referenced plants or historical results.
- Stations: create/update station metadata (name, category, process label and location) with validation. Historical lab sample rows/import provenance remain immutable to browser editing; update the import workflow through separately validated import jobs.
- Model configuration: versioned plant thresholds and emission factors, required canonical units, source/reference and applicability notes. Values must be finite and valid for their domain. Unsupported or unsourced factors cannot silently be labelled validated. Changes apply to future runs only; immutable previous run snapshots retain their original values and references. The panel cannot change model equations, validation status or decision-use policy.
- History: paginated audit records of administrative changes, with actor, time, reason and resource; exclude credentials/session tokens and do not expose citizen notes/photos in the admin list.
- Status: read-only readiness/dependency status and release acceptance checklist. Keep secrets, SSH, database passwords, signing keys, SMTP credentials and API/identity trust origins in deployment configuration. No arbitrary shell/SQL or secret editor in the web UI.

## Security and data boundary

Introduce server-owned `platform:admin` capability and require both it and verified operator MFA on every admin read/write endpoint. Browser mutations use existing session/CSRF protection. No public account listing or unauthenticated configuration writes. Bootstrap/grant administration only through the trusted CLI. Changes require a human reason and append-only AuditEvent evidence in the same database transaction. Use row locking/expected revision to prevent silent lost updates; refuse stale edits with an actionable conflict. Validate all fields server-side and return field errors to the editing form.

Add a small persisted configuration revision/provenance record through an Alembic migration instead of encoding mutable scientific provenance only in UI text. Snapshot resolved thresholds/factors/units/references into runs and reject incompatible comparisons. Public plant/station reads must not expose private account/admin data.

## User experience

Use existing typography, green tokens, controls and responsive page patterns. Each view has a clear title, bounded table/search, edit form, explicit Save action, required change reason, success/error status and no misleading enabled controls for unauthorized users. Scientific settings display units and reference next to the field. Preserve unsaved input on failed requests. Destructive/historical actions are absent from this release. Link to report moderation and documentation.

## Acceptance

- Anonymous/nonadmin/no-MFA requests fail closed; CSRF, self-elevation and stale-update tests pass.
- Native-account changes are audited and revoke sessions; legacy account claims remain separate.
- Plant/station fields and threshold/factor provenance survive reload; invalid/unsupported/nonfinite inputs are rejected.
- A historical run is unchanged by a later configuration edit; new runs record the new revision; comparison reports differences.
- Browser verification at desktop/mobile includes role gates, validation focus, save/reload, errors and history.
- DB migration upgrade/downgrade/schema check, OpenAPI generation, backend/frontend tests, lint and builds pass.

## Separate release gates

Production needs approved server access/domains, real identity/mail/private storage, restores/load/alerts/rollback and physical-device acceptance. Scientific validation needs plant datasets, independent calibration/held-out validation and review. Neither is marked complete by adding this panel.

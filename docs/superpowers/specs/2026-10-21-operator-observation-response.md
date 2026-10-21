# Operator verification and response to citizen observations

Status: approved and implemented in source/local staging21October2026. Production and operational-team acceptance remain pending.

## Purpose

Make citizen observations actionable within the platform while keeping publication moderation, operational response and scientific validation distinct. An approved public summary does not mean an incident is resolved, and an operator inspection is not automatically scientific ground truth.

## Scope and approach

Add an Operations reports view to the existing protected operator dashboard. Reuse citizen report IDs, plant/station registry and account identity. Store a separate append-only response history with current workflow state, rather than editing the original citizen observation. Support both legacy and versioned records, clearly labeled.

Alternatives considered: adding a single Resolved checkbox to publication moderation loses assignment/inspection evidence; building a separate ticketing system duplicates identity and report context. A focused platform response workflow is recommended.

## Workflow

An operator with explicit response permission and MFA can acknowledge a report, assign it to an eligible operator, optionally associate a plant/station, record an inspection and close/reopen with a reason. States: Unassigned, Assigned, Investigating, Closed. Assignment is explicit; viewing a report does not acknowledge it. Each transition records actor, server time and reason with optimistic concurrency to reject stale changes. Inspection time is separate from entry time.

Inspection result: Confirmed, Not confirmed, Unable to verify. Require a concise method/evidence note and observed time; Not confirmed does not retroactively invalidate the citizen report. Action record describes what was done or why no action was taken. Closing requires a recorded disposition; reopening preserves history. Avoid automatic priority, hazard severity or SLA assertions until plant teams approve their rules. No automatic emergency dispatch or equipment control.

Association with a plant/station identifies the team's investigated service context; it is not proof of cause. Initially operator-selected from the existing registry. Do not infer catchments from proximity without reviewed catchment geometry. Do not claim a public complaint was caused by a nearby treatment plant.

## Permissions, privacy and identity

Introduce server-enforced report:respond capability with operator MFA. It is granted using existing protected administration with required reason; no self-elevation. Only eligible responders appear in assignment choices. Reading response history and private report evidence requires authorized responder/reviewer access. Operational notes, assignees, private photo/location and linkage remain out of public community responses. No citizen notification messages are sent by this subsystem.

Users retain ownership of original reports; no operator edit to citizen measurement values. Administrative audits and response transitions are committed atomically. Plant deletion/history rules remain intact. Disable access promptly on permission removal.

## Research use

Retain report protocol/revision, original context, linked follow-up IDs, inspection time/method/result, action history and explicit QA status. Publication status, inspection result and researcher validation must be separate fields. This first workflow records inspections; it does not certify instruments, create a validation dataset automatically or invent numeric accuracy thresholds.

A controlled research export will require its own access scope, field allowlist, dataset version, provenance, exclusions and ethical/privacy review. Scheduled repeat observations and independent reference sampling remain study procedures, not inferred absences from the public map.

## Operational limits

This supports awareness, investigation and accountability. It is not plant SCADA, a full maintenance-management system or a substitute for live flow/process measurements, laboratory quality control, approved operating procedures and trained staff. Sensor ingestion, freshness alerts, staffing escalation rules and research exports are separate work. The existing illustrative simulation remains prohibited for operational decision use.

## Acceptance

Server tests: responder/MFA/CSRF gates, restricted assignment, stale conflicts, transition requirements, append-only history, foreign/private access, atomic audits and unchanged original observations. Dashboard tests: assignment/inspection/action/closure, preserved inputs on failure, permission loss and no misleading resolution from moderation. Local integration uses marked synthetic records only. Production hosting and field-team acceptance remain open.

# Operator response to citizen observations

The existing dashboard now provides `/dashboard/operations`, separate from public-summary moderation at `/dashboard/moderation`. This workflow supports investigation/accountability; it does not control plant equipment, replace operating procedures or establish scientific accuracy.

## Access and deployment

Apply Alembic revision `a61c84b0e921` after `e43b2c90ab01` before deploying the new API/UI. It adds private report response state and history without rewriting citizen records. The responder capability is `report:respond`; grant it with a reason through protected administration or the trusted account CLI. Initial administrator grants remain server-only. Every operations read/write and private linked photo read requires authorized access and MFA. Browser writes retain CSRF/origin checks. Capability alone does not satisfy MFA.

The response APIs live under `/api/v1/operations`: paginated reports, individual report/history, eligible responders and minimal plant/station choices. Registry reads expose only IDs/labels to responders, avoiding an unnecessary administration grant. Publication moderation retains its own `report:review` permission. Role removal revokes browser sessions; subsequent access fails closed.

## Daily workflow

1. Open Operations reports and filter by Unassigned, Assigned, Investigating or Closed. New reports have virtual unassigned state/revision0 until a response is recorded. Reports appear regardless of publication status.
2. Acknowledge to begin investigating, or assign an eligible operator. Reading a case does not acknowledge it.
3. Optionally associate an existing plant/station as investigation context. Association does not establish that a nearby plant caused the reported condition. No catchment geometry or automatic attribution is configured.
4. Record an inspection: Confirmed, Not confirmed or Unable to verify; actual inspection time; and method/evidence. Entry time is recorded separately by the server. An inspection is not certified ground truth, and Not confirmed does not rewrite the citizen's answer.
5. Record actions taken. Close with a disposition after an inspection or action exists. Closed cases require Reopen before further changes. All steps require a reason and append history.

Each accepted mutation increments an expected revision. The server locks the original report before checking that revision and commits response state, history and audit together. Stale requests409. The UI retains typed text, reloads the case and requires explicit acknowledgment of the refreshed history before retrying. A failed refresh cannot unlock submission; selecting the same queue row does not bypass review. An uncertain write may have completed: inspect the updated timeline before taking further action.

## Evidence and privacy

Private case detail shows the original citizen record, observation/submission times, exact location, protocol or legacy context, private note/photo, assignment, registry association and response history. The original observation and publication status are unchanged by response actions. Legacy records retain unspecified historical measurement context. Operational history, identities and notes are absent from public community output. Do not paste secrets or unnecessary personal information into reasons/evidence notes.

Inspection evidence in this release is a text note and the existing citizen photo link; there is no new operator-photo upload, attachment chain of custody or research export. No automatic priority, response-time target, sensor freshness alarm, citizen notification or dispatch is configured. Teams must define their operating procedures, staffing/escalation and evidence requirements before relying on this for routine operations.

## Verification and limits

Automated tests cover responder/MFA/CSRF gates, stale revisions, assignment eligibility, registry validation, closure/reopening, unchanged publication/original payload, atomic event/audit counts and permission removal. Dashboard tests include a real rendered-page failure/review guard and account-change privacy regression. The disposable migration upgrade/downgrade/upgrade and Alembic schema check pass. Actual simultaneous-writer/load acceptance remains open; sequential stale tests and code review are not load evidence.

See the Samsung acceptance record for local citizen workflow results. Production hosting, backups/restores, operational-team acceptance, physical accessibility and research reference validation remain separate release gates. The illustrative simulation remains prohibited for operational decision use.

### Local acceptance — 21 October 2026

The existing synthetic QA identity completed actual password/TOTP operator sign-in. A server-audited responder grant enabled the operations view; no administrator capability was granted. In the browser, the Samsung's synthetic flooding update was assigned, inspected as Unable to verify (explicitly no field inspection), given a synthetic action, closed and reopened. History advanced through revisions1–5 while publication remained Pending. A separate sequential mutation advanced revision6, then submitting the stale browser form returned409, reloaded the case and preserved text with submission locked until explicit review. At390px viewport the page had no horizontal overflow and the primary form button measured approximately44px high. This is software/local workflow evidence, not field-team or simultaneous-load acceptance.

After explicit refreshed-history acknowledgment, the synthetic case closed at revision7, still Pending publication. The temporary responder grant was removed through trusted audited administration; browser sessions were revoked and the next protected read hid private case/form content. The QA citizen account retains its original non-responder permissions.

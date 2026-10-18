# Interface and backend acceptance — 2026-10-18

Status: repository improvements verified; full shared-platform production release is not accepted. This record supersedes stale capability inventories in the older deployment proposal. No production endpoint, published APK, existing staging identity or data was changed.

## Source and environment

Worktree: `monash-platform-interface-launch`, branch `feat/interface-launch-readiness`, starting commit `531984a`. Exact implementation commits are in branch history. Python 3.12.13, Node 22.22.1, lockfile installs. Database verification uses only `monash_test` on loopback 5433. Frontend production preview is local; T3 connects through the environment address. Browser API responses are injected from `scripts/browser-fixtures/monitoring.js`, not real observations.

## Verified changes

- Laboratory mean/max exclude missing and below-detection records, disclose quantified/total count, and preserve measured zero. Missing results do not become zero. Failure is distinct from empty results, with Retry preserving filters.
- Account navigation explains availability. Login/register routes no longer offer disabled registration actions. Home has one download entry, an actual release-specific app screen and concise research/reference access.
- Search by plant name/code works alongside the map. Plant markers are named buttons with safe text nodes. Panels fit 320px, move focus to Close and return it on dismissal; Escape closes the panel. Decorative camera motion honors reduced motion.
- Line charts use a modular SVG runtime with line/legend/title/tooltip/threshold/maintenance support. Optional station charts and workspace views load when requested. A production-preview adapter failure was reproduced, covered by a render regression test and corrected to use the package's ESM export.
- The imported index.html favicon change is recorded as an explicit adaptation. The page title now says Monash Water. Hash verification remains active for unadapted source files.
- Compatible source-map-js 1.2.2 lockfile patch removes the reported high-severity build-tool advisory; no broad dependency upgrade.
- Readiness now checks configured private bucket access and identity signing-key availability as well as database revision. Outages return a generic 503 without private details; liveness remains separate. DB connect/pool waits are bounded at two seconds; database probe statement timeout is two seconds, external probes use two-second network waits and storage retries are disabled for readiness. This is not a hard end-to-end deadline or a complete dependency acceptance test.

## Verification evidence

- Frontend: 20 tests pass, ESLint passes, TypeScript/production build passes. Tests include real chart SVG output, chart-adapter rendering, public route rendering and numeric summaries.
- Python: 96 pass, one skip; API/report ownership/privacy/idempotency, MFA/token/revocation, run provenance/failure, backup-envelope integrity and restore-target refusal are covered. These are synthetic tests; the skip requires original legacy source checkouts.
- T3 preview: desktop and 320/390px station panel, search/no-match, focus movement/return, Escape, all-BDL summary and outage-to-mixed-value retry were exercised. Public desktop/mobile captures inspected; narrow-screen download/research/references/login/register routes have no horizontal overflow. Final review found mobile focus escaping behind the panel; responsive dialog/inert background was added and both Tab directions, Escape/focus restoration and portaled metric selection were retested. Production chart renders after selecting a station; the 3D bundle is absent from the initial map journey.
- The Playwright smoke scripts were updated to current contracts; this session used the product-native T3 preview instead of launching a separate browser runner. Full assistive-technology, optional 3D rendering/full simulation UI and physical Android checks remain open.

## Loading measurements

Same environment and production preview, from home to synthetic monitoring, using browser Resource Timing `encodedBodySize` for JavaScript including the map worker. These samples were captured after modularization and before the final mobile-focus refinement. This is a payload comparison, not a controlled latency benchmark, exact final artifact-size inventory or full page-weight total.

| Journey | Before | After | Result |
| --- | ---: | ---: | --- |
| Public entry JS | 105,723 bytes | 104,864 bytes | Essentially unchanged |
| Cumulative home → map JS | 947,542 bytes | 536,070 bytes | About 43% less |

Before selecting a station, the updated map did not request the station chart, ECharts or 3D bundle. Chart dependencies are fetched when a laboratory panel opens. Large map/3D/chart chunks still trigger Vite's size warning; no claim of complete performance optimization.

## Read-only staging checks

Existing staging API readiness returned 200 and identity discovery returned 200. The image was `sha256:27310170ef13ec6a53bac1b838187fbc78d74bba5e6046dd6ef36b36f0630e27`; it is not a deployment of this branch. Storage port 3900 refused connections. `monash-staging-storage-1` is exited; Docker reports its Garage configuration bind mount points at a missing/incompatible file under a former worktree. No storage keys/configuration were regenerated and no volume was reset.

Earlier logs show a past local empty-bucket restore exercise, but that is not current off-server recovery evidence. This run did not repeat a full backup/restore while storage was unavailable.

## Remaining acceptance gates

| Gate | Required next evidence |
| --- | --- |
| Staging storage | Restore original configuration from custody, repair the stale mount and verify bucket permissions/upload/download without replacing keys |
| Integrated identity | Real registration/mail verification/recovery, invited operator MFA and revocation through both clients against the release environment |
| Data migration | Authorized private export, reconciled counts/identifiers/media hashes and privacy/ownership checks; no ownership inferred from matching email |
| Capacity/rate controls | Initial audience is estimated at 20–50 people; confirm peak active users and photo rate/size, then establish request/concurrency controls and measure reads/uploads/simulations |
| Recovery | Name an accountable restore owner and agreed acceptable data loss/downtime; test encrypted off-server app/identity/object restoration and measure actual results |
| Operations | Concrete redacted logging/alerts, notification recipient, incident access and exercised failure/recovery |
| Production routing | Approved API/account domains/hosting; exact TLS/proxy/callback/cookie/CSRF/media/cache checks before replacing the legacy Vercel destination |
| Android release | Existing signing identity, increased versionCode, physical-device fresh install and cross-version upgrade, OIDC callback/offline/photo retry |
| Release and rollback | Reviewed immutable artifacts, migration/write-freeze procedure, preservation of post-cutover writes, rollback triggers and acceptance window |

User input on 2026-10-18: estimated 20–50 people. A recovery owner means the person with responsibility and access to restore service/data; no owner or RPO/RTO has yet been confirmed. No production domains/hosting or peak concurrency are assumed.

Scientific decision use remains prohibited: `effluent_v1` is illustrative and unvalidated, regardless of software test results.

## UI consistency follow-up

The monitoring map, scenario workspace and moderation page now share `OperatorHeader`, including platform branding, monitoring navigation and current-surface context. The existing public palette/font remain canonical. Operator cards use flat borders, moderation uses shared primary/danger buttons, account blocks share the same typography/radius, and shared controls have a 44px minimum height on phones. Workspace view buttons expose their selected state. Public and operator layouts retain different density appropriate to their tasks.

The workspace stacks settings, visualization and results below the desktop breakpoint instead of forcing three columns onto a phone. Workspace API failure now offers Retry rather than asserting that the plant does not exist. Moderation has a clear empty state/retry path; unbroken private notes wrap without widening the page. Desktop and mobile T3 checks used a temporary static preview with synthetic same-origin API responses; no private accounts or reports were accessed. Workspace/moderation widths 320/390/1280px and a 500-character unbroken note were checked. The note overflow was reproduced before the fix and absent afterward.

Current frontend verification: 22 tests pass, lint and production build pass; the pinned client import tests also pass. Prior backend result remains 96 passed/one skipped; this follow-up changes frontend code only. Native Android consistency on the signed release and full assistive-technology checks remain open.

## Resolve before launch, in order

1. **Restore staging storage.** Recover its original private Garage configuration and repair the obsolete worktree mount without replacing keys or resetting volumes. Needed input: access to the original configuration/backup custody.
2. **Confirm production hosting and addresses.** Supply the approved API and account domains and hosting access; prepare TLS, database, identity, private storage and the real browser proxy/callback configuration. Existing Vercel routes still point to legacy services.
3. **Agree recovery responsibility and limits.** Name the person responsible for restoring service and choose acceptable data loss and downtime. Rehearse encrypted off-server restoration of app/identity databases, objects and required configuration/keys.
4. **Pass integrated staging acceptance.** Test registration/email/recovery, invitations/MFA/revocation, report/photo/retry/moderation/privacy, monitoring and scenarios through both clients. Any private legacy import requires an authorized export and reconciliation.
5. **Qualify the small-user deployment.** Use the 20–50-person estimate, confirm peak simultaneous use and photo volume, configure rate/concurrency controls and redacted alerts, then measure latency/error/resource behavior. Total registered users alone does not specify peak load.
6. **Qualify Android and scientific scope.** Build the API-connected APK with the existing signing identity and higher versionCode; test physical installation/upgrade, sign-in and interrupted uploads. Keep simulations illustrative; decision use requires a separate validation record.
7. **Review and release the exact artifacts.** Merge/deploy the reviewed UI and backend/client artifacts only after their applicable gates pass, rehearse rollback preserving new writes and observe an acceptance window. The web UI can be reviewed independently; this feature branch is not yet the public deployment.

## Scientific audit and twin removal

The unsupported twin, its timeline state and deck.gl dependencies have been removed from the active frontend; 47 packages were removed. The remaining workspace views are Effluent Trends and Scenario Comparison. Frontend tests/lint/build and a T3 production-view check confirm the twin is absent. This does not complete the proposed workflow/comparison redesign.

The [simulation evidence audit](../science/SIMULATION_EVIDENCE_AUDIT.md) identifies uncalibrated effluent coefficients, methane-factor provenance gaps for ANAMMOX/AGS, equation/terminology ambiguities and comparison-integrity defects. Those findings are open scientific acceptance issues, not evidence that calculations were corrected or validated. Existing simulation semantics and public CSV values were preserved pending scientific review. The proposed configure/run/inspect/compare redesign is awaiting the user's design response.

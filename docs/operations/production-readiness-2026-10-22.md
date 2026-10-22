# Production preparation review — 22 October 2026

Production rollout is paused. This review starts from `eb4b399` on `main`, with changes isolated on `audit/production-readiness-2026-10-22`. The running local stack is synthetic staging. Public HTTPS health/placeholder routes do not constitute a production API or identity deployment. No client cutover, production account registration or signed mobile release is authorized by these checks.

The first release targets **open public registration**, as confirmed by the project owner. Treat abuse prevention, email verification and capacity controls as launch requirements; the earlier 20–50-person planning estimate is not an access restriction or a public-load guarantee.

## Checklist and evidence

| Area | Result | Evidence and limit |
| --- | --- | --- |
| API, database, identity permissions, reporting, administration, operational response, simulations | Checked in disposable environment | 246 Python tests passed, one optional original-source-checkout test skipped; test PostgreSQL only on loopback 5433 |
| Migration | Checked | Upgrade and drift check; head `b72a05e3c114`; no schema changes in this review |
| API contract | Checked | Generated OpenAPI unchanged; production proxy regression now covers every documented v1/v2 path |
| Dashboard | Checked | 50 tests, lint and production build; large map/chart chunks remain a performance concern |
| Mobile | Partially checked | Flutter 3.44.7 analyzer and 59 tests pass; this ARM64 host cannot execute standard x86-64 AAPT2, the supported-host GitHub workflow passed its debug APK build on `804e4f8`; physical-device acceptance remains open |
| Dependency advisories | Checked at audit time | Vite 8.1.6, Pillow 13.0.0 and Certifi 2026.10.19; full dashboard npm audit and exported locked Python runtime pip-audit report no known vulnerabilities; this is not a container/OS security audit |
| Provenance and repository policy | Checked | Imported-target verification and repository policy checks; optional original source checkouts are absent |
| Scientific reproducibility | Checked, not validated | Research notebook executes against 154 final-effluent samples, snapshot 1.1.0; no model equations or factor semantics changed |
| Main documentation | Corrected | API/architecture descriptions, JDK requirement, production routing/settings and methane recovery caveat reconciled to source |
| Public manual | Separate working branch | Refresh pinned source/OpenAPI, workflow pages, historical screenshot labels and evidence coverage in `monash-platform-docs`; its own checks are recorded there |
| Earlier API image | Built, not deployed | ARM64 image `sha256:2602e4369d715a5b98e4aba535134ac5be7c2ad5caa618cc8559e4bf48fdba18`; running staging retains its prior image |
| Local staging | Existing synthetic environment | API, identity, databases and storage are present; readiness is dependency health, not end-to-end acceptance |
| Recovery | Local rehearsal only | See the recovery evidence below; no off-server production recovery claim |
| Production launch | Blocked | External and operational gates below are still open |

The automated suites include unauthorized/ownership/MFA/CSRF cases, idempotency, public privacy projections, malformed data, immutable run provenance, migration reversal/reapplication and readiness failure paths. They use synthetic data and doubles where documented. Passing these suites is not a penetration test, live mail test or physical-device test.

## Defects resolved in this review

- Production Caddy routing omitted `/api/v2`, preventing current observation workflows from reaching the API. Both committed proxy examples now preserve v1/v2, with a schema-driven regression check.
- Malformed persisted comparison containers could cause HTTP 500. They now return structured 422 `incompatible_runs`; no model calculation changed.
- Body-limit responses omitted the documented request ID. Correlation now begins before the limit middleware and the 413 envelope matches its response header.
- Production settings accepted HTTP storage, credential-bearing storage URLs, path-bearing browser origins, mismatched callback origins and HTTP CORS/backchannels. They now reject those configurations; a reviewed HTTPS backchannel remains supported.
- The production template did not expose the existing account-settings feature flag. It now defaults false; enabling it requires provisioned and accepted identity flows.
- Dependency audits found Vite, Pillow and Certifi advisories. Targeted updates are locked, and CI now audits dashboard development dependencies and Python runtime dependencies. [Pillow's release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html) document the major-version security fixes.
- The local restore helper now waits past PostgreSQL’s temporary initialization server; a startup-sequence regression prevents restoring against that transient server.
- Interrupted media downloads now close their S3 response stream. Backup reads are bounded before allocation and close responses on success/failure; restore reads are bounded to the expected object size.
- Current documentation described implemented identity/storage/reporting as future work and the manual described obsolete mobile navigation. Current behavior is separated from historical artifacts and unperformed acceptance.

## Recovery evidence

An encrypted local backup was created after pausing staging API/identity writers, then those services were restarted. The archive contains 18 application and 230 identity tables and zero photo objects. A disposable restore reconciled both database table manifests and authenticated configuration. The first restore attempt failed at `pg_restore`; four diagnostic reruns reconciled successfully. Inspection found that the Unix-socket readiness probe could accept PostgreSQL’s temporary initialization server before it shuts down. The helper now waits for final-server TCP readiness; a regression fails on the old helper and passes on the correction, and three subsequent real restores reconciled successfully. The initial stderr was not surfaced, so its precise cause cannot be proven; capture private diagnostics on any recurrence. The initial empty-bucket rehearsal did not prove media restoration. A follow-up added one uniquely named synthetic PNG, paused writers for backup, restored both database manifests and that object, checked its SHA-256 and denied anonymous reads (HTTP 403) on source and restored buckets. The fixture was removed afterward. The post-stream-fix restore took 17.19 seconds for 18 application tables, 230 identity tables and one 82-byte PNG. This tiny local fixture does not establish recovery of production volume, application ownership authorization or restored identity sign-in. The archive/key remain on this host; off-server disaster recovery is still open.

## Bounded read-load evidence and public-access limits

An isolated API process from the current checkout served 200 loopback reads at concurrency 10 against synthetic staging data: 200 HTTP 200 responses, p50 49.31 ms, p95 225.17 ms and maximum 333.39 ms. Routes covered plants, models, one-page station data and v1/v2 community projections. Total elapsed time was 1.45 seconds. This was a short smoke check on a shared host during audit work, not sustained public capacity, mixed uploads/simulations, network latency or an agreed service-level objective.

The existing 11 MiB body limit and worker/database connection bounds do not provide per-client abuse quotas, global buffered-body admission control or a total body-read deadline. Open registration also needs protection at the identity/edge layer, including mail abuse and account-farming controls. API-only throttling cannot protect authentik enrollment endpoints. Define trusted proxy handling before using client-IP limits; never trust arbitrary forwarded headers. Quotas across replicas require shared state or an edge service.

## Gates that must remain open

- [ ] Project owner names deployment, recovery, incident and scientific-review owners; assign actual CODEOWNERS and approval responsibilities.
- [ ] Approve stable API/account origins and real transactional email. Request a project subdomain and approved mail relay/sender through the supervisor and Monash IT, or approve an independently owned domain/provider. A personal Monash address is not DNS ownership.
- [ ] Provision production identity claims, exact callbacks, verified enrollment, MFA and shared settings; test actual delivery, recovery, email changes and old-session revocation.
- [ ] Build/scan immutable release images, review OS/container dependencies, configure separate migration/runtime DB permissions, private storage and secret custody. Existing running images do not automatically include this branch's fixes.
- [ ] Agree retention/deletion and abuse-response policies for reports/photos; measure and enforce request, upload, simulation and account quotas against an agreed load envelope.
- [ ] Name RPO/RTO and rehearse an encrypted off-server restore with nonempty private media, identity sign-in, ownership, denied anonymous access and a measured recovery time.
- [ ] Configure redacted alerts for readiness/errors, disk/storage, backup age and certificates; deliver a test alert to an actual owner and exercise restart/reboot behavior.
- [ ] Reconcile authorized lab/private legacy exports and ownership. Do not infer legacy anonymous ownership from email or equate source compliance fields with current permit compliance.
- [ ] Test both clients against the intended release: registration/login/recovery; report/photo/retry; v1/v2 moderation and privacy; operational response conflicts; monitoring and scenarios; keyboard/screen-reader/narrow-screen behavior.
- [ ] Build Android on a supported host, preserve signing identity, increment versionCode, and test physical install/upgrade, permission denial, account switching and interrupted uploads.
- [ ] Cut over the dashboard same-origin proxy only after acceptance; keep API responses uncached and verify callback, cookies and CSRF through that proxy. Rehearse rollback preserving writes since cutover.
- [ ] Keep all simulation outputs illustrative/unvalidated. Scientific decision use needs approved provenance, equation interpretation, calibration, held-out validation, uncertainty and independent authorization.

## Features worth adding after the foundations

| Priority | Feature | Acceptance criterion |
| --- | --- | --- |
| Before launch | Operational health and capacity controls | Named owners receive actionable redacted alerts; agreed load stays within latency/resource budgets; rejected work returns predictable retry responses without duplicate writes |
| Before launch | Retention and deletion workflow | Policy-approved retention, auditable deletion, orphan reconciliation, and backup-retention implications are tested without exposing other users' records |
| Next | Durable offline report drafts | Encrypted account-scoped drafts survive app restart; bounded storage, visible retry state and stable idempotency prevent duplicate reports; logout/account changes protect private drafts |
| Next | Citizen status notifications | Opt-in updates distinguish publication from operational response; messages contain no private location/photo details and honor unsubscribe preferences |
| Next | Observation quality and review assistance | Flag missing context, possible duplicates and stale reference revisions without silently deleting evidence or treating flags as scientific validation |
| Next | Operator workload and response summaries | Filter assignments/age and inspect audit events; exports respect capabilities and exclude private data by default |
| Later | Performance and accessibility improvements | Measure map/chart startup on target devices; reduce bundle cost; qualify TalkBack, keyboard, contrast and large-text layouts |
| Separate research programme | Calibrated models and uncertainty | Site-approved influent/flow/process data, traceable factors, independent validation and bounded intended use; preserve historical runs' original validation status |

Shared settings, map-first reporting, flooding follow-ups, moderation and operational response are already implemented. The roadmap should extend them rather than count them again as proposed features. Each new feature needs a bounded design and acceptance criteria before implementation.

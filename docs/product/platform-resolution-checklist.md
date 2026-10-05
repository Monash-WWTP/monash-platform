# Platform resolution checklist

This checklist tracks readiness across the public website, operator dashboard, CitizenFlood Android app, API/identity, scientific methods and release operations. A source-level implementation is not production evidence. Keep an item open until its acceptance evidence is linked and an accountable owner records the result.

## Completed in repository source

- [x] Use the public landing page's canonical palette and Manrope across the public and operator browser surfaces.
- [x] Use shared semantic warning, success and danger roles for dashboard alerts and severity badges.
- [x] Use equivalent canonical green, charcoal, muted text, pale surface and divider colors in Android Material 3.
- [x] Replace report-category emoji with Material icons in category selection, form headings, map markers, map details and report lists; expose category names once to screen readers.
- [x] Keep the supplied urban-water carbon-accounting guideline PDF byte-identical in the public web build, link it directly from the landing page, and list citation, DOI, license caveat and relevance on the reference page.
- [x] Label the scenario influent input BOD₅ while preserving the legacy API wire property and its description.
- [x] Subtract CH₄/N₂O recovery terms directly as written in the referenced equations; retain illustrative/unvalidated status and prohibit decision use.
- [x] Add browser token parity and Android icon/theme widget coverage.

## Website functionality

| Route or flow | Current behavior/source state | Acceptance still required | Status |
| --- | --- | --- | --- |
| `/` landing page | Public route presents CitizenFlood, research and the supplied PDF reference. | Deploy the reviewed source; test direct PDF open/download on desktop and mobile; confirm all landing links work. | [ ] |
| `/download` | Reads a validated release manifest; an unavailable artifact must not render a misleading download action. Current public 1.0.0 APK metadata is documented separately. | Verify unauthenticated artifact download, checksum display, install guidance and release manifest against the exact signed APK. | [ ] |
| `/research` and `/research/:slug` | Article collection is approval-gated; no unpublished drafts should enter public imports. | Verify approved-only content, source links, corrections, responsive citations and withdrawal/correction procedure on the deployed site. | [ ] |
| `/research/references` and hosted PDF | Reference citation and PDF are included in repository source. The PDF states CC BY-NC-ND 4.0 and notes possible third-party rights. | Confirm actual hosting/distribution is within rights terms; check DOI resolution, PDF response headers, mobile reading and accessibility on production. | [ ] |
| `/login`, `/register` | Pages disclose that shared account integration is not available from the public portal. | Keep copy aligned to real identity deployment status; verify no credential flow is implied before it exists. | [ ] |
| Keyboard and responsive access | Public page has skip link, visible focus, reduced-motion rules and narrow-screen layout rules in source. | Check all public routes at keyboard-only, screen-reader, desktop and narrow viewport; record contrast and overflow evidence. | [ ] |

## Dashboard functionality

| Route or flow | Current behavior/source state | Acceptance still required | Status |
| --- | --- | --- | --- |
| `/dashboard` map | Shows treatment plants and separates approved community observations from lab/plant data; includes map fallback and observation loading/error/empty states. | Against intended API and production permissions, verify plant/station selection, community toggle, privacy rounding, retry and map-unavailable fallback. | [ ] |
| `/dashboard/plants/:plantId` | Provides monitoring, scenario and results workspace; scenario routes still include legacy `/api/*` dependencies per dashboard README. | Point at the intended versioned API; verify lab filters, scenario create/edit/run/failure state, immutable run provenance, comparisons and no synthetic data presented as live. | [ ] |
| `/dashboard/moderation` | Operator moderation route exists in source. | Verify invitation/MFA gate, list pagination, approve/reject actions, audit trail, duplicate submissions and community projection privacy against staging/production. | [ ] |
| Dashboard identity and authorization | Shared account pages are not integrated; production dashboard proxy still targets the legacy service. | Verify operator invitation, MFA, expiry/revocation, least privilege and fail-closed API authorization using direct unauthorized API requests. | [ ] |
| Browser visual/accessibility parity | Shared tokens, font and semantic chart colors are now in source. T3 preview snapshots failed on the original and a fresh tab, so there is no screenshot evidence yet. | Inspect actual desktop/tablet/mobile dashboard captures; verify chart contrast, keyboard operations, labels, focus and reduced-motion behavior. | [ ] |

## CitizenFlood Android functionality

| Screen or flow | Current behavior/source state | Acceptance still required | Status |
| --- | --- | --- | --- |
| Report category selection | Four categories use distinct Material icons with labels. | Check on supported physical Android device, large text and TalkBack. | [ ] |
| Numeric readings and plant condition | Rainfall, water level and temperature collect numeric values; wastewater collects Normal/Warning/Critical. | Verify invalid values, range/unit expectations with domain owners, validation copy and back-navigation persistence. | [ ] |
| Location and photo | Report flow captures location and can select camera/gallery photos. | Test denied/revoked permissions, unavailable GPS, low accuracy, large/unsupported images, upload interruption and privacy/retention behavior. | [ ] |
| Sign-in, submit, retry | Source flow requests a verified session and uses an idempotency key for submission retries. | Verify deployed identity/session expiry, repeated taps, lost responses, photo retry and report visibility using staging without synthetic production submissions. | [ ] |
| Map and profile | Native map lists recent reports, provides retry and profile/session actions. | Verify empty/error/offline states, category labels, map accessibility, account recovery/logout and approved-vs-pending visibility on device. | [ ] |
| Signed app distribution | CitizenFlood 1.0.0 is published against the existing legacy backend; current source contains shared API/OIDC work. | Build a new reviewed release only after endpoint cutover; install/update-test on physical devices; compare signature, version, artifact URL, byte size and checksum. | [ ] |

## API, identity, data and privacy gates

- [ ] Deploy successor FastAPI, application PostgreSQL, identity provider and private object storage with approved DNS/TLS, secret injection, restricted DB networking and least-privilege roles.
- [ ] Move dashboard and Android source clients to the approved versioned contract without silently changing the published APK's legacy behavior.
- [ ] Complete issuer/subject identity mapping, verified citizen registration, operator invitation/MFA, recovery, session expiry/revocation and fail-closed authorization.
- [ ] Reconcile migrated accounts, reports, media references and access controls; never claim legacy anonymous reports by email alone.
- [ ] Prove citizen observations, lab samples and model outputs remain distinct in API contracts, storage, projections and UI.
- [ ] Verify approved public community output removes private identity, free-text notes, precise coordinates and private media paths.
- [ ] Exercise report/photo upload, moderation, pagination, retry, rate limits, request tracing and failure handling against the production-like service.

## Science and publication gates

- [x] Keep `effluent_v1` marked `illustrative_unvalidated` with `decision_use_permitted=false` until the gates below pass. Scientific decision use remains blocked.
- [ ] Record carbon inventory boundary, process scope, influent load measurements, units, sampling provenance, censoring, factor sources, regional/process applicability, GWP source/time horizon and recovered-gas evidence.
- [ ] Reconcile equations against the full approved method; the current code only follows the arithmetic of guideline WWTP Equations 5.25 and 5.28 and is not a complete inventory.
- [ ] Complete independent process/mass-balance review and quantify uncertainty; generic default factors remain assumptions until supported.
- [ ] Separate calibration data from held-out validation; report residuals, uncertainty, operating-regime applicability and versioned independent review.
- [ ] Keep plant control, legal compliance and certified inventory uses prohibited until a versioned scientific acceptance record explicitly authorizes them.
- [ ] Maintain reference citation, DOI, rights/attribution caveat, correction history and an explicit statement that citing the guideline does not validate the simulator.

## Deployment and operations gates

- [ ] Assign named maintainers and owners for identity, privacy/retention, science, publication, Android signing, backups and incident response.
- [ ] Decide software licensing and hosting/publication rights with the relevant owner.
- [ ] Record request/photo volume, resource limits, worker counts, retention, RPO/RTO and recovery owners.
- [ ] Configure structured redacted logs, request IDs, health/dependency checks, alerting and latency/error/resource monitoring.
- [ ] Back up application and identity databases, objects, configuration and key recovery metadata independently with agreed encryption/retention.
- [ ] Restore into an isolated environment; reconcile schema, row counts/checksums, issuer-subject mappings, media references and authorization; record achieved RPO/RTO.
- [ ] Rehearse migration rollback and compatible client/artifact rollback before production cutover.
- [ ] Run unauthenticated public route/PDF/download checks, authorized operator workflows, mobile report/photo tests, API smoke tests and privacy checks after deployment.
- [ ] Record exact source commit, deployed artifacts, environment, test evidence, acceptance owner and rollback point for each release.

## Evidence record

For each checked release gate, add the evidence URL or repository path, test environment/date, exact source/artifact revision, responsible reviewer and any limitations beside the item. A source build or automated test alone does not prove production integration or scientific validity.

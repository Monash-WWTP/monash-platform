# Cross-Platform Consistency and Readiness Design

## Goal

Bring the public website, operator dashboard, and CitizenFlood Android app into one coherent product experience based on the existing landing page design, resolve repository-level functional defects found in the readiness audit, and provide evidence-based acceptance checklists for release gates that cannot be completed from source changes alone.

## Approved direction

The landing page design is the canonical visual reference. Retain its deep green action color, white ground, charcoal and muted green-gray text, pale green grouped surfaces, Manrope type hierarchy, flat surfaces, thin rules, compact rectangular actions, and visible focus treatment. Extend this visual language to the operator dashboard and Android app while preserving each surface's native interaction patterns and information hierarchy.

This is an operational product UI, not a marketing redesign. Preserve current product scope, copy truth, data meanings, and route behavior unless a documented defect requires a correction. Replace category emoji throughout the Android reporting flow with a consistent, accessible icon mapping. Use the dashboard's existing Lucide icon package and Flutter Material icons; do not add icon dependencies.

## Scope and decomposition

This work is divided into four deliverables with separate acceptance evidence:

1. **Shared design system:** establish one canonical token set derived from `DESIGN.md` and the landing page styles; apply it to the public portal, operator dashboard, and Android app, including map/chart semantic colors and accessible status states.
2. **Client experience and functionality:** audit each existing route and user flow, correct repository-level defects, consistent labels and error/loading/empty states, and make checklists of remaining client/API contract gaps. Keep legacy endpoints and production behavior explicit until the successor API cutover is configured and verified.
3. **Scientific rigor and publication:** keep the simulator explicitly illustrative unless independent data and scientific review support a stronger claim. Document equation coverage, input provenance, uncertainty, model boundary, calibration and held-out validation requirements. Preserve the supplied publication reference and PDF availability; do not imply that citation alone validates the simulator.
4. **Release and operations readiness:** maintain an owner-action checklist for identity, server deployment, data reconciliation, privacy, monitoring, backups/restore, Android release, rollback, and production smoke evidence. Checklists can be made complete as documents, but a gate can only be marked passed when its evidence exists.

## Shared design system

Canonical values and roles remain sourced from the existing landing-page `DESIGN.md` and `public.css`; remove the competing stock dashboard palette and the app's independent brand seed/background. Define shared semantic roles for primary action, on-surface, muted text, surface, grouped surface, border, focus, success, warning, danger, map categories, and chart series. Where a platform cannot share a file format, mirror the same named values and add a parity check or documented mapping.

Use Manrope across browser surfaces and a bundled/available matching family on Android only if licensing and packaging are already satisfied; otherwise use the Android native sans-serif while matching weights, scale and line-height roles. Retain native Material navigation and controls. Category iconography must be consistent between category selection, report form, and map/list representation; icons need semantic labels, and color is never the sole carrier of category or severity.

## Client experience and functionality

- Inventory public routes, operator routes and Android screens, with entry, primary action, data source, permissions/authentication, success, empty, loading and error behavior recorded for each.
- Resolve directly fixable UI and interaction defects, including truthful BOD5 labeling, retry/idempotency behavior, missing-data messaging, accessible names, responsive overflow and category icon consistency.
- Preserve current routing and data meanings. Do not silently switch endpoints or remove legacy paths.
- Keep public sign-in/register copy honest until shared identity is actually integrated.
- Identify client/API mismatches and produce cutover acceptance items from the migration roadmap; do not claim an integrated workflow merely because mocks/builds pass.

## Scientific and publication integrity

The model remains `illustrative_unvalidated`, with decision use disabled. The available guideline informs the current CH4/N2O arithmetic only; it is not a complete carbon inventory, a calibrated process model, nor independent validation. Clearly label assumptions/defaults in the interface and in saved run provenance. Retain source, units, time basis, factor/GWP version, recovery terms and model version for each run where contracts support it; document missing fields that require API/data migration.

Acceptance for scientific decision use is outside code-only scope and requires: agreed boundary; representative measured influent and operational data with analytical provenance and censoring; sourced region/process-appropriate factors; mass-balance and conservation review; calibration data separated from held-out validation; residual and uncertainty analysis; applicability limits; independent review and a versioned acceptance record. Until then outputs cannot support plant control, legal compliance or certified inventory claims.

The supplied PDF remains directly available from the landing page and reference list. Preserve its citation, DOI, license and third-party rights caveat. Do not modify the PDF or imply an endorsement by its publisher or authors.

## Release and operational gates

Repository changes can prepare configuration and documentation, but production release acceptance requires evidence for each item below:

- Successor API, identity provider, PostgreSQL and private object storage deployed with approved domains, TLS, secret injection, access controls and monitoring.
- Dashboard and mobile use the intended versioned API contracts; old clients and legacy data are reconciled before cutover.
- Identity registration/recovery, operator invitation/MFA, issuer-subject mapping, expiry/revocation and fail-closed authorization tested against staging and production settings.
- Citizen reports, photos, moderation and community projections verified end to end; private notes, identities, precise locations and media paths do not leak.
- Backups include database and media/configuration dependencies; isolated restore evidence meets owner-set RPO/RTO; rollback and migration reversibility are rehearsed.
- Android artifact is signed, reproducible, publicly downloadable, integrity-checked and install/update-tested on physical devices. Existing emulator evidence does not replace these cases.
- Production smoke checks pass for public routes, operator routes, mobile reporting, API health, monitoring and error reporting.
- Named owners accept software licensing, privacy/retention, scientific-use policy and incident response.

No public deploy, production data mutation, identity migration or scientific approval is implied by this design approval. Those actions require their own release evidence and, where applicable, owner decisions.

## Verification

For code changes, run focused checks for each changed client/service, then the repository policy/manifest checks and relevant builds. Verify browser behavior at desktop and narrow widths, native Android analyze/tests and a real-device visual pass where available. Verify design parity from actual captures rather than token inspection alone. Existing automated tests prove software behavior only; they do not prove live integration, production readiness or scientific validity.

## Out of scope

- Claiming that the platform is production-ready before all release gates have evidence.
- Deploying backend infrastructure or migrating live identities/data without configured environments and owner acceptance.
- Enabling scientific decision use or describing the engine as fully implementing the guideline.
- Replacing current products, changing institutional branding, adding new features or publishing new research content.
- Removing legacy APIs, source repositories or routes before migration reconciliation and rollback acceptance.

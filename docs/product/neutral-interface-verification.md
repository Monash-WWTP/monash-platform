# Neutral interface and progressive disclosure — 19 October 2026

User request: remove the documentation's Platform source shortcut, use a neutral palette, add a landing image and reduce dashboard/app clutter without losing functionality.

## Implementation

- Neutral white/charcoal/grey chrome across the web and Android source. Warning, danger and success retain their meaning. Controls, charts and focus use shared tokens; input boundaries have a distinct neutral tone.
- Monitoring retains latest sample/date, BDL/missing notation, parameter selector, trend and the legal-screening caveat. Filters, summary statistics, sample rows and methods are expandable. Active filters and community-layer status remain visible in disclosure summaries, including unavailable/loading states.
- Maintenance, equipment and carbon assumptions use labelled native disclosures with configured-state summaries. Their controls remain mounted, preserving draft values and validation behavior.
- Android photo/note controls expand on request and report attached/entered state. Native widget tests exercise closing/reopening with a note intact. Reading/location/submit remain visible. Recent map readings expand, preserving every original row/marker action. Long observation details scroll.
- A generated river landscape accompanies documentation entry, labelled illustrative and AI-generated. The actual published APK screenshot remains release-specific. Asset prompt/provenance: `apps/dashboard/public/assets/illustrations/README.md`.
- The separate documentation site removes the Platform source navigation shortcut, retains collapsed implementation evidence, uses neutral light/dark themes and the same illustrative landscape.

## Verification scope

Dashboard: 34 tests, lint, TypeScript/production build. Repository: 27 tests passed, one legacy-checkout test skipped; policy and 207 pinned-source checks passed. Flutter: 14 tests including optional-field state retention; analyzer clean. Native report forms were rendered at 390×844 with synthetic GPS using a temporary widget preview; this is not physical-device acceptance. Temporary preview code is excluded from the change.

Browser verification uses a separate local read-only fixture server with synthetic plant/sample records. These records are not production measurements. The disclosure controls retain BDL notation and sample rows and fit the inspected desktop/phone widths. API identity, storage, simulation equations and data contracts are unchanged. GitHub CI and Vercel deployment are verified separately during delivery.

The published signed APK remains immutable; these Android source changes require a qualified future signed release and device acceptance before public distribution. This work does not approve scientific decision use or production backend cutover.

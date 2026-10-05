# Cross-Platform Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the landing page visual system to the dashboard and CitizenFlood app, remove category emoji, resolve directly fixable user-flow gaps, and leave a complete evidence-based checklist for release gates.

**Architecture:** The website's canonical CSS values stay authoritative in `apps/dashboard/src/index.css`, with public-page rules consuming the same named tokens. Dashboard semantic chart/map styling maps to these tokens. Flutter mirrors the same semantic palette in `AppTheme` and maps each report category to a Material icon. A product checklist records implemented repository acceptance separately from external release evidence.

**Tech Stack:** React, Tailwind CSS v4, Lucide, Flutter Material 3, Node test runner, Flutter test, Markdown.

**Spec:** `docs/superpowers/specs/2026-10-05-cross-platform-consistency-and-readiness-design.md`

## Global Constraints

- Landing page palette and typography are the shared visual source of truth.
- Do not add UI/icon dependencies.
- Preserve routes, product behavior, API meanings and native controls.
- Category and severity meaning must not depend on color alone.
- Keep simulator status `illustrative_unvalidated` and decision use disabled.
- Do not claim production integration or validation without runtime evidence.
- Keep the supplied reference PDF byte-identical and its rights caveat visible.

## Review Focus

- Public portal styles and operator dashboard styles must resolve to identical semantic token values; test their shared token contract.
- Dashboard chart and map category colors must remain readable and semantically distinguishable; check their palette mapping and one desktop/mobile browser capture.
- Android report category must remain understandable without emoji; widget-test icons, labels and semantics for all categories.
- Screens must still convey loading, empty, error and retry outcomes; add these to the route/screen acceptance matrix and verify existing targeted flows.
- Release and science gates must remain visibly open unless supporting evidence exists; inspect the finished checklist against current deployment and validation documents.

---

### Task 1: Canonical browser tokens and dashboard palette

**Files:**
- Modify: `apps/dashboard/src/index.css`
- Modify: `apps/dashboard/src/pages/public/public.css`
- Modify: `apps/dashboard/src/components/dashboard/chartPalette.ts`
- Modify: `apps/dashboard/src/components/comparison/ComparisonView.tsx`
- Modify: `apps/dashboard/src/pages/MapPage.tsx`
- Test: `apps/dashboard/tests/design-tokens.test.ts`

**Interfaces:**
- Consumes: canonical `DESIGN.md` colors and self-hosted `/fonts/Manrope.ttf`.
- Produces: browser custom properties `--brand-ink`, `--brand-muted`, `--brand-rule`, `--brand-green`, `--brand-green-hover`, `--brand-soft`, and `--brand-white`; shadcn semantic variables map to those values. Public styles consume the same properties. `CHART` is the shared chart semantic palette.

- [x] **Step 1: Write failing token contract tests** asserting the canonical hex values, Manrope application, dashboard variable mapping, and that public CSS consumes the shared properties.
- [x] **Step 2: Run `npm --prefix apps/dashboard test -- --test-name-pattern='canonical browser tokens'`; confirm it fails because the browser token contract is not present.**
- [x] **Step 3: Implement the root semantic tokens, Manrope font application, public variable consumption, chart palette, and map marker colors using the agreed canonical values.**
- [x] **Step 4: Run the focused token tests and full dashboard tests; confirm all pass.**
- [x] **Step 5: Run dashboard lint and production build; confirm both pass.**

### Task 2: Android palette and category icon system

**Files:**
- Modify: `apps/citizenflood/lib/theme/app_theme.dart`
- Modify: `apps/citizenflood/lib/models/report.dart`
- Modify: `apps/citizenflood/lib/widgets/category_tile.dart`
- Modify: `apps/citizenflood/lib/screens/report_form_screen.dart`
- Modify: `apps/citizenflood/lib/screens/map_screen.dart`
- Test: `apps/citizenflood/test/widgets/category_tile_test.dart`
- Test: `apps/citizenflood/test/models/report_test.dart`

**Interfaces:**
- Consumes: the browser token contract from Task 1 and Flutter Material 3.
- Produces: `ReportCategory.icon` (`IconData`) for Rainfall, Water level, Temperature, and Wastewater plant. `AppTheme` uses equivalent primary, neutral, surface, border, focus, and status color roles.

- [x] **Step 1: Write widget/model tests** that assert every category has a labeled, accessible Material icon in the category tile and that category icon mapping is distinct and non-empty.
- [x] **Step 2: Run the focused Flutter tests; confirm they fail because category tiles and form/map headings use emoji.**
- [x] **Step 3: Add the category icon mapping and replace emoji usage in category selection, report form title, map detail and map list. Give map markers the shared green action color and preserve category identification via the icon.**
- [x] **Step 4: Map the Flutter theme to canonical landing-page colors and matching neutral surfaces/radii while retaining Material navigation/control behavior.**
- [x] **Step 5: Run focused tests, full Flutter tests, and `flutter analyze`; confirm all pass.**

### Task 3: Platform functionality and release resolution checklist

**Files:**
- Create: `docs/product/platform-resolution-checklist.md`
- Modify: `docs/product/portal-acceptance-checklist.md`
- Modify: `apps/dashboard/README.md`

**Interfaces:**
- Consumes: route inventories, current mobile screens, `docs/operations/deployment.md`, `docs/migration/ROADMAP.md`, and `docs/science/VALIDATION.md`.
- Produces: a checklist with status, owner/evidence fields, and explicit completion criteria for public website, dashboard, Android, API/identity, data/privacy, science/publication, and operations. Items already verified in source are checked; live or owner-dependent gates stay open.

- [ ] **Step 1: Add the checklist skeleton and route/screen acceptance rows** for each user entry point, main action, data source, permission requirement, success, empty, loading, error and retry behavior; leave all evidence-dependent items unchecked.
- [ ] **Step 2: Review every row against current routes, screens, deployment documentation and science status; add precise evidence requirements and mark only completed source-level items checked.**
- [ ] **Step 3: Update existing portal acceptance links to the unified checklist and keep individual release procedures as detailed sources.**
- [ ] **Step 4: Run repository policy and docs/link checks; confirm the checklist is internally consistent and no production or scientific gate is marked passed without evidence.**

### Task 4: Cross-surface visual and functional verification

**Files:**
- Modify only findings from Tasks 1–3.

- [ ] **Step 1: Start the Vite preview and inspect desktop and narrow-screen public routes plus the dashboard map/workspace through the T3 preview.**
- [ ] **Step 2: Run the repository's public portal and dashboard map browser smoke checks; fix only defects exposed by the approved scope.**
- [ ] **Step 3: Run the cross-surface palette/icon audit and confirm no report-category emoji remain in app UI.**
- [ ] **Step 4: Run repository policy/manifest checks, dashboard tests/lint/build, API/simulator checks affected by the prior commit, and Flutter tests/analyze.**
- [ ] **Step 5: Record any live-infrastructure or empirical-evidence gates still open in the resolution checklist; do not publish a new APK or production website from this plan.**

## Commit strategy

Keep the shared browser theme, native icon/theme, and acceptance checklist in separate conventional commits on `feat/cross-platform-consistency`. Do not merge or publish this feature branch until verification is complete and the user reviews the concrete result.

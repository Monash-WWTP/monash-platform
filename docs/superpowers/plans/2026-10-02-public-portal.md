# Public Portal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add the approved public water-atlas landing page, honest Android distribution page and approved-content research section to the existing dashboard application.

**Architecture:** Public routes and operator routes share the web deployable while application data remains behind the shared API. Public release metadata and research content are independently validated, versioned inputs; absent integrations produce explicit unavailable states. Identity is a separate work package and must not be simulated by local forms.

**Tech Stack:** Existing React, TypeScript, Vite and React Router; semantic HTML/CSS and locally served assets/fonts.

**Spec:** `docs/product/public-portal-deliverables.md`; approved composition `.impeccable/mocks/atlas-purpose-index.png`.

## Global Constraints

- APK downloads and published research are public and require no account.
- Citizen registration requires verification. Operator access requires invitation and MFA.
- Research content may be published only after approval.
- Existing synthetic debug APK is not a public release.
- Simulation outputs are illustrative and unvalidated.
- No page code before Impeccable's current asset/production-plan checkpoint passes.
- Preserve native execution chosen by the user. The final build requires a fresh review.

## Review Focus

- A missing release must not produce a broken or misleading download link.
- Direct private-repository URLs and non-HTTPS release links must never become public download targets.
- Unapproved research drafts must not enter the public bundle.
- Old plant deep links and workspace back navigation must remain usable after route migration.
- Keyboard and narrow-screen visitors must retain all public actions without overflow or misleading map controls.

### Task 1: Public layout and route separation

**Files:** Create `apps/dashboard/src/pages/public/LandingPage.tsx`, `PublicLayout.tsx`, `public.css`; modify `apps/dashboard/src/main.tsx` and workspace map links.

**Interfaces:** PublicLayout renders an Outlet; LandingPage consumes availability metadata and links to download/research/account/workspace routes.

- [x] Complete measured spec, artwork generation and required asset review; keep all text/controls semantic.
- [x] Add a browser regression check for old plant links and back-to-map navigation, showing it fails before route migration.
- [x] Implement `/`, `/download`, `/research`, `/research/:slug`, `/login`, `/register`, `/dashboard`, `/dashboard/plants/:plantId`; preserve legacy plant links with deliberate redirects.
- [x] Render identity entry points as integration unavailable until real OIDC/session endpoints exist; no fake registration or local account persistence.
- [x] Implement approved layout with local font/artwork, accessible navigation and responsive reading order; map controls only if they manipulate the illustration and disclose that it is illustrative.
- [x] Verify desktop/mobile screenshots, route links and existing dashboard behavior. Keyboard focus styles are present; comprehensive assistive-technology QA remains a production gate.

### Task 2: Honest release metadata and installation guide

**Files:** Create `apps/dashboard/src/releases/release.ts`, `release.test.ts`, `pages/public/DownloadPage.tsx`.

**Interfaces:** `Release` holds versionName, versionCode, minAndroid, publishedAt, byteSize, sha256 and artifactUrl; `parseRelease(input: unknown): Release | null` rejects invalid public metadata. `currentRelease` is null until a verified release is published.

- [x] Write failing tests for absent release, invalid checksum/version/size, HTTP URLs and private repository download links.
- [x] Implement strict metadata parsing; never infer availability from a button or placeholder filename.
- [x] Implement unavailable state and Android system-confirmation instructions; desktop users can copy the download-page URL, with QR code only when the public URL is configured.
- [x] Verify an absent release creates no active APK link; document later signed artifact publication and real-device install/update gates.

### Task 3: Approved research content

**Files:** Create `apps/dashboard/src/research/articles.ts`, `articles.test.ts`, `pages/public/ResearchPage.tsx`, `ResearchArticlePage.tsx`.

**Interfaces:** `PublishedArticle` holds stable slug, title, authors, publishedAt, type/status, sources, approval and accessible content; `publishedArticles` initially empty. Draft source lives outside public bundle imports.

- [x] Write failing tests for unapproved items, duplicate slugs and missing attribution/source metadata.
- [x] Validate published metadata and keep drafts out of the build entry points.
- [x] Implement honest empty index, missing-article page and accessible approved article layout, citations and correction history.
- [x] Do not manufacture demonstration papers or metrics.

### Task 4: Verify and hand over

- [x] Run the public regression checks, `npm run lint`, TypeScript checks and production build.
- [x] Capture desktop/mobile, fix material findings in a bounded batch and run the applicable Impeccable detector and fresh finish review.
- [x] Document visual tokens and approved composition in DESIGN.md and its sidecar through the Impeccable documentation workflow.
- [x] Record tested behavior and pending identity/APK/server gates without claiming deployment or release.

Identity implementation, client API cutover, release signing and server deployment each require their existing architecture work packages; this plan does not substitute placeholders for those deliverables.

## Execution evidence and scope

Implemented on `docs/public-portal-deliverables`; content tests consolidated in `apps/dashboard/tests/public-content.test.ts` (9 tests). Backend/repository suite: 57 pass. Public and map production browser checks pass. User waived further viewport approval rounds; Impeccable hero state remains open, not passed. Current review state and production gates are documented separately. Research/release fixtures are tests only, never public demo content.

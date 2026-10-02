# Public portal review state

Date: 2026-10-02
Branch: docs/public-portal-deliverables

Confirmed: public downloads and articles; verified citizen registration; invitation-only operator access; one account with distinct permissions; approved research content only; visual concept first.

Direction selected: public water atlas, direction seed 4da37c5e, option assigned. Selection returned by the direction board. Final composition approved in chat: layout 1, atlas with purpose index.

Composition review: `.impeccable/atlas-compositions.json`; question key 8e574f6a. Local board initially served at http://127.0.0.1:43083/. This URL depends on the local process; restart through Impeccable if unavailable.

First composition: `.impeccable/mocks/decision/assigned.png`.
Additional compositions: `.impeccable/mocks/atlas-directory.png` and `.impeccable/mocks/atlas-rail.png` (generated, inspected and available on the review board).

Build state opened at comps. Do not write application UI before the final visual approval and subsequent Impeccable gates. This work has changed documentation/configuration only. Existing dashboard behavior and identity migration are unchanged.

Potential generated text must be reviewed against PRODUCT.md: no unsupported live monitoring, validated models, papers, operational claims or institutional endorsement. The illustrative map is not a source of geographic truth.

## Approved composition and production preparation

The user selected layout 1 in the ChatGPT iOS chat. Its approved copy is `.impeccable/mocks/atlas-purpose-index.png`, with approval recorded in its sidecar. Build state advanced through comps and spec; the plates check reports only the required production-plan/asset review pending.

Measured inventory: `.impeccable/build/spec.json` (41 regions; one raster artwork; text and controls semantic). Headline font ranked as Gelasio 400 at the measured cap height. Production artwork: `assets/plates/atlas.png`, regenerated from the approved crop with UI removed and prompt provenance embedded.

Asset review session: `6ba81dc3e01f9f248d79718aac2856a7fc8cfa477c0167d77ec6ba73e74918ab`; local review URL initially http://127.0.0.1:40867/. Remote iOS access cannot use localhost. A structured chat question presents the actual artwork and semantic production plan; its answer is pending. Do not fabricate a review receipt or silently bypass the component-review gate.

Implementation plan: `docs/superpowers/plans/2026-10-02-public-portal.md`. No application UI has been edited yet.

## Implementation checkpoint

The user replied “Okay” to the production asset/plan approval question. That chat approval was applied to the local component-review UI, and its receipt allowed the plates gate to advance. This records the user's decision, not an independent visual approval by the agent.

The public landing viewport and shared public layout are implemented, using the regenerated map and locally served OFL-licensed Gelasio font. Illustration controls change the illustrative image only. The `/dashboard` route is introduced; full route separation and legacy redirects are not complete.

The hero comparison reached 90% overall but flagged typography/control differences after three attempts. Per Impeccable, iteration stopped and the actual built viewport was displayed in chat. The new viewport approval question is pending. No hero approval or gate pass is claimed.

Release metadata and approved research validators have seven passing tests; the initial missing implementation produced four failing tests before implementation. `npm run lint` and `npm run build` pass. The Node distribution lacks native TypeScript support; tests use the installed tsx development dependency. The build reports an inherited large dashboard bundle, which should be separated from the public route through lazy loading during route completion.

The browser portal contract check initially failed on the absent landing heading as expected. It remains incomplete because download/research/account routes and legacy redirects are not implemented yet. Do not report end-to-end portal completion.

Pending next work: viewport approval; finish public routes; release availability wiring; approved research renderer; old plant/back-map compatibility; responsive/browser verification; fresh final review and design documentation. No real identity integration, signed APK distribution or server deployment has occurred.

## Current verified delivery checkpoint

The user instructed “Move on do work” after the viewport question. This supersedes further design approval rounds. The hero gate remains open after the 90% comparison; no additional human approval receipt or Impeccable gate pass is claimed. Earlier chronological checkpoints above describe their state at that time.

Implemented public routes, lazy operator routes and legacy plant redirects. Signed APK absence disables downloads; shared identity absence is explicit; research starts empty. Release manifests validate release notes as well as URL/version/checksum metadata. Approved research validates and renders limitations and correction history. Desktop users can copy the download page URL; clipboard failure has explicit guidance. Mobile illustration legend now appears on request.

Fresh finish review identified four material gaps (mobile legend, limitations/corrections, URL handoff, release notes); all were addressed. Intermediate 1101/1200px overflow checks now pass with shrinkable introduction text and wrapping headings. Detector ran once with no findings. Production captures: `.impeccable/review/desktop.png` and `mobile.png`.

Verification: 9 frontend metadata tests, ESLint, TypeScript/production build, public production-browser contract, existing synthetic map browser contract, and 57 backend/repository tests pass. Public entry JS is approximately 330 kB uncompressed / 104 kB gzip; large operator chunks remain a performance limitation. Browser tests block external services and do not demonstrate live login, production data access or Android installation.

Remaining product work: real shared identity in both clients, successor API cutover, production APK signing and distribution, approved publication content, and standalone server deployment/restore/release verification. This checkpoint delivers the public portal source, not those production services.

Fresh review disposition after fixes: “ship this portal scope”; no remaining material findings. Reviewer independently reran 9 frontend tests and inspected refreshed captures and changed contracts. DESIGN.md records the actual public visual system; it does not extend the legacy operator UI's styling.

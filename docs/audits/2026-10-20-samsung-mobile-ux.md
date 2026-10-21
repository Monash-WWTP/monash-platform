# Samsung mobile UX audit and proposed direction

Status: original pre-redesign audit. The approved implementation and measured device results are recorded in [Samsung acceptance](../operations/samsung-mobile-acceptance-2026-10-20.md); findings below describe the initial interface. Device: Samsung SM-A076B, Android16, current staging debug APK built from64c9144. Existing product green retained. Findings combine device screenshots with source review; TalkBack, large-text, landscape and full authenticated reporting remain unverified.

## Observed priorities

1. P0: identity flow remains on an indefinite authentik Loading screen after the user's sign-in attempt. Returning to the app and token/account completion are not proven. Local community API measured200 in0.005s; this does not explain the stalled identity page. Diagnose the actual flow request/redirect before changing timeouts or attributing it to debug overhead.
2. P1: category grid labels lack examples, required measurement/unit context and a way to resolve uncertainty. Temperature/water-level observation subject is not explained. Plant condition defaults to Normal and supplies no criteria distinguishing Warning/Critical. Users can unknowingly submit the default. Any guidance must describe citizen observation rather than invent a validated plant assessment.
3. P1: submission lacks a separate final review showing type, value/unit, time, actual location accuracy and photo/note. Confirmation and history must show pending review versus approved publication. Preserve existing retry idempotency and identity fencing.
4. P1: account screen has no explicit busy state or structured canceled/verification/network error treatment; account FutureBuilder uses loading copy even on failed fetch. Group identity details/actions apart from product information. Do not render role implementation details as the primary citizen explanation.
5. P1: unbranded dark authentik flow breaks continuity with the restrained green app. Use supported brand logo/title/favicon/CSS variables and flow layout for sign-in, registration, verification, recovery and MFA. Keep browser-based OIDC/PKCE and the existing identity provider; do not build a separate password form into Flutter.
6. P2: large square category tiles consume the phone viewport while communicating little. Prefer compact descriptive choice rows with icon, title, one-line example and clear navigation affordance. Selected form choices need visible checked state, explanatory text and accessible selected semantics.
7. P2: current map differs technically and visually from dashboard. Flutter uses flutter_map and raster OSM; dashboard MapLibre GL JS uses https://tiles.openfreemap.org/styles/liberty. Share style/data semantics through native MapLibre integration; do not embed the entire dashboard. Start mobile in usable2D, with consistent legends, selected marker detail sheet and explicit private/public observation distinction. Preserve privacy rounding, ownership and logout camera reset. Verify style/provider suitability, attribution, connectivity and device performance before qualifying replacement.

## Proposed user flow

Report / Map / Account navigation. Report asks what was observed using descriptive choices, then shows category-specific fields and units, location with permission/accuracy state, optional photo/note, and a Review report action. Review lists all submitted values and offers Edit or Submit. Plant-condition selection is explicit (no silent Normal default); explanatory criteria require domain agreement. After success show report reference and Pending review state, with access to My reports. Returning from sign-in preserves the draft.

Map uses the same MapLibre style family as dashboard with native mobile controls, loading/error/retry state and data-source legend. Citizen observations remain distinct from laboratory stations/plants. No 3D-first interaction or scientific equivalence is implied.

Account uses a compact branded header, clear Sign in/Create account entry, verification status and My reports when authenticated; loading/cancellation/errors are actionable and bounded. Identity service pages carry matching green/white tokens and CitizenFlood/Monash Water naming, with a clear return path. No credentials/secrets enter the app code or docs.

## Acceptance before completion

Fix the stalled flow; measure sign-in stages separately. Test fresh/repeat login, cancellation, registration/email verification, reset and return-to-app. Test category comprehension, explicit condition selection, review/edit/submit, permission denial, photo attach, failed upload retry without duplicates, offline/resume, logout/account-switch privacy, TalkBack selected state, large text/keyboard/back, mobile map style failure and Samsung interaction performance. Profile/release performance is separate from current debug build. No cloud deployment or public APK release is implied.

## Sources

- apps/citizenflood/lib/screens/category_screen.dart
- apps/citizenflood/lib/widgets/category_tile.dart
- apps/citizenflood/lib/screens/report_form_screen.dart
- apps/citizenflood/lib/screens/profile_screen.dart
- apps/citizenflood/lib/screens/map_screen.dart
- apps/dashboard/src/pages/MapPage.tsx
- https://docs.goauthentik.io/customize/branding/
- https://docs.goauthentik.io/customize/interfaces/flow/
- https://github.com/maplibre/flutter-maplibre-gl

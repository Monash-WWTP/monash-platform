# Mobile UX and shared login follow-up

Scope: CitizenFlood on branch feat/mobile-map-first, checked-in source, recent Samsung screenshots and completed device report journey; operator login checked live against local staging. This audit does not certify production deployment. The Samsung was locked throughout this follow-up; fresh physical keyboard, landscape and TalkBack checks could not be completed. The user was asked to unlock it. No new application UI changes were made during this audit.

## Login evidence

Mobile: the previous Samsung run completed enrollment, email confirmation and browser sign-in, returned to CitizenFlood, displayed the verified synthetic account, and uploaded/submitted a synthetic photo report appearing Pending in My reports. The empty Android taskAffinity callback defect was fixed and guarded by a regression test.

Operator dashboard: opened Administration on localhost8180, followed Sign in to the dedicated monash-operator authentication flow, entered the same synthetic account, configured TOTP and completed a subsequent password/TOTP challenge. Callback returned to /dashboard. /api/v1/auth/me returned200 with the synthetic account and report:own only; /api/v1/admin/status returned403. This verifies shared identity, MFA and denial of ungranted administration; it does not verify privileged operator actions with an invited operator account. First-time TOTP setup required repeating identification/password before the subsequent challenge; this onboarding friction needs a focused flow review.

The public Vercel operator deployment still uses the previously configured backend. New shared-account production acceptance is pending provisioning and configuration; local success must not be described as production sign-in acceptance.

## Native audit verdict

The interface reads as a native Android app: Material navigation, standard form controls, native popup menu, bottom sheets and system Back. The primary citizen task is coherent: explore map, choose a report type, confirm a point, enter observation, review, submit, see Pending. Three destinations and a four-choice reporting menu keep the visible decision set small. Labels remain valuable; replacing report types or form actions with icons alone would increase ambiguity.

Provisional source/evidence score:12/20. Accessibility2/4 (map-symbol semantics gap), performance2/4 (avoidable marker regeneration, release timing unmeasured), appearance3/4 (consistent green/white and Material hierarchy, some fixed map colors), platform conformance3/4 (native controls, physical edge cases unverified), adaptivity2/4 (narrow200% text tests pass, physical landscape/keyboard coverage incomplete). This is an audit estimate, not a user-study score. Two P1 and five P2 findings; no new confirmed P0 application failure. CI did reveal a build-tool mismatch, separately corrected to Java21; native MapLibre declares source/target21.

## Findings

### P1 — Map observations lack a reliable accessible alternative

Location: lib/maps/citizen_map.dart, native MapLibre symbols/onSymbolTapped. Production markers are native symbols; the labeled Flutter IconButtons exist only in the widget-test adapter. There is no always-accessible observation list for all displayed public/owner markers. A screen-reader user may be unable to discover and open map observations even though widget tests pass. Add a labeled observations-list action with category, time, ownership and approximate-location context, while retaining marker taps. Verify with physical TalkBack. Suggested workflow: $impeccable harden.

### P1 — Observation semantics require clarification

Location: lib/screens/report_form_screen.dart; lib/models/report.dart. Normal/Warning/Critical are selectable but do not identify what the citizen should observe to distinguish them. Water level supplies metres without explaining its reference; rainfall supplies millimetres without establishing a collection interval. Users can submit a technically valid number or enum with incompatible meaning. This is a data-quality problem, not a reason to add a long tutorial. Agree concise category-specific labels/context with the domain owner; use optional detail where necessary. Do not invent validated thresholds or silently change scientific semantics. Suggested workflow: $impeccable clarify.

### P2 — Location confirmation is primarily coordinates

Location: lib/screens/location_picker_screen.dart. The center pin and explicit confirmation are good, but raw coordinates and Selected point provide little recognition of the intended street/place. Consider a concise place label or search backed by an approved geocoder, keeping coordinates as detail/fallback. Choosing a current point or moving the map remains available. No geocoder was configured in this audit. Suggested workflow: $impeccable shape.

### P2 — Icon-only + needs first-use discoverability validation

Location: lib/widgets/report_menu.dart. New report tooltip and four labeled choices are present; the menu is compact and visually confirmed above the button on the Samsung. A bare + still requires a first-time user to infer its purpose. Validate that people find it; if they hesitate, use a compact Report label alongside the icon. Avoid a permanent instruction banner. Suggested workflow: $impeccable clarify.

### P2 — Operator identity naming leaks implementation terms

Location: infra/staging/identity/bootstrap.py, Application naming. The live operator page included “Monash Water monash-operator” in its continuation sentence. Rename the provider application to a human-facing dashboard name, and check first-time MFA setup does not unnecessarily restart identification/password. Compact logo and short headings now render cleanly. Suggested workflow: $impeccable distill.

### P2 — Marker assets are regenerated unnecessarily

Location: lib/maps/citizen_map.dart, didUpdateWidget/_draw. Every ready-widget update clears/recreates symbols and generates eight64px category/ownership PNGs. Cache style assets per controller and redraw observations only when relevant data/selection changes; camera changes should not regenerate category assets. This is a source-level inefficiency; no claim of measured release-mode jank is made. Suggested workflow: $impeccable optimize.

### P2 — First-time operator MFA setup repeats credentials

Location: live monash-operator-authentication flow, AuthenticatorValidateStage configure path. The synthetic account configured TOTP, then returned to identification/password before reaching the configured authentication-code challenge. The subsequent password/TOTP callback worked. Review the configure-and-resume path before operator onboarding acceptance; do not weaken MFA to remove the extra step. Suggested workflow: $impeccable harden.

## Wording and layout assessment

The map is no longer overloaded with prose: compact observation count, location control and + reporting menu. Three bottom labels establish where the user is. The menu’s four labels are necessary, not clutter. Account secondary information is collapsed; the sign-in heading and action are brief. Review’s location/time/value/note/photo and Pending status are useful confirmation, even though they contain more text than the map. Keep these.

The largest remaining copy gap is meaningful observation context, not general verbosity. Do not remove units, confirmation actions, pending/rejected status, location accuracy, accessibility labels or error recovery merely to reduce word count. Recent portrait screenshots fit cleanly; automated320px/200% text layouts and menu reduced-motion interaction pass. Physical landscape, IME and TalkBack remain unverified here.

## Recommended order

1. $impeccable harden: accessible map list and operator configure/resume flow.
2. $impeccable clarify: domain-reviewed measurement/condition context and + discoverability.
3. $impeccable shape: recognizable location selection without adding a verbose guide.
4. $impeccable optimize: cache marker assets after behavior is settled.
5. $impeccable polish: one final physical layout confirmation after those changes.

These can be addressed separately or as one scoped pass. Do not infer release acceptance from this audit; rerun the affected device checks after implementation.

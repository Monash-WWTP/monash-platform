# CitizenFlood integrated mobile experience

Status: navigation and interaction direction approved by owner; updated written design for review. Scope: existing Flutter Android app and authentik user-facing flows; dashboard remains web-hosted on Vercel, cloud backend provisioning deferred. Preserve existing green product identity and owned logo assets. Do not invent institutional endorsement, measurement validity or scientific classification.

## Intent

A citizen can identify the current task, select an observation or map marker, enter a report, review it and understand submission/account state without lengthy guidance. Visual hierarchy, selected states, native controls and consistent navigation carry the explanation. The Samsung SM-A076B Android16 is the first physical acceptance device.

## Navigation and reporting

Keep three native destinations in this order: Map, My reports, Account. Open Map first. Report creation is the primary Map action, not a separate destination. Consistent top app bars, insets, type scale, spacing and green action/selection tokens. Replace oversized category squares with compact icon/title choices and brief unit labels only where necessary. Selecting an existing observation opens its detail sheet; it does not silently choose a new report location. Use current location or explicitly enter a centre-pin location picker, move the map beneath the pin and confirm the place before Report here. The selected category remains visible in the form and review. Preserve existing categories and numeric/condition semantics; do not invent new condition criteria. Plant condition requires explicit selection, with checked state and accessible announcement rather than silent Normal default.

Separate observation details, location and attachments using clear hierarchy. Show location acquisition/permission/error state and accuracy when available; never promise a captured location before it exists. Photo/note remain optional, with visible attachment state. Review displays category, recorded value/unit or condition, time, location and attachments; Edit returns to the retained draft. Submit locks one snapshot and preserves the existing idempotent uncertain-retry logic. Success presents Pending review and a route to the user's reports, not an implication of public approval. Login and cancellation preserve the draft.

## My reports

A dedicated destination lists only the authenticated citizen's submissions with observation type, time and Pending/Approved/Rejected status. Tapping opens full owner details and any review reason. Empty, loading, refresh failure and signed-out states are explicit. Approved public observations remain a separate privacy-reduced projection. Account switches clear prior owner data. Anonymous map exploration remains available; submission and private history require sign-in.

## Map

Use native MapLibre through a maintained Flutter binding, sharing the dashboard's OpenFreeMap Liberty style and compatible data semantics, subject to provider/style/device acceptance. Do not embed the dashboard WebView. Mobile begins in2D; location/zoom/attribution controls stay reachable. Native rendering must preserve private/public ownership boundaries and logout camera reset.

Tapping an observation icon selects it visibly and opens a bottom sheet containing observation identity, time, value/status and location context. Only one selected marker; matching list/detail selection stays synchronized. Allow selection of overlapping markers through clustering/disambiguation. Device location has a distinct symbol and accuracy treatment; observation pins must not imply the user is at that location. Public rounded locations remain visibly distinct from precise owner records. Empty/loading/tile-failure/offline states are actionable.

## Account and identity

Account groups identity/verification status and primary account actions; report history belongs to My reports. Product information is secondary. Signed-out state has clear Sign in/Create account actions. Busy, canceled, unverified, expired and unavailable states are distinct, bounded and retryable. Avoid repeating administrative capability details in citizen copy.

Keep external-browser OIDC/PKCE and authentik password/MFA handling. Use product logo/name/favicon, green/white palette, matching type/spacing and supported brand variables/flow layouts across login, registration, confirmation, recovery and MFA. Do not replace identity security with custom native password handling. Registration email confirms/activates the account; recovery email alone requests a new password. Correct template separation now (confirmed defect), while full return-to-app verification remains required. All tokens and secrets stay out of assets/docs.

## Functional and accessibility gates

Diagnose the observed indefinite authentik loading state independently of visual changes. Measure browser flow, callback, token exchange and account loading separately; do not attribute it to debug builds without evidence. Confirm verification link continues enrollment without asking for a replacement password; recovery does reset and revoke sessions. Test fresh/repeat/canceled login and return to draft.

Verify TalkBack labels/selected states,48dp targets, large text, keyboard, portrait/landscape and Samsung Back. Exercise location/camera denial, photo attach/upload, offline/uncertain retries without duplicates, background/resume and account-switch privacy. Check map style errors, overlap selection and native rendering performance. Rebuild/install staging APK for acceptance; signed public release and production cloud acceptance remain separate.

## Delivery

Implement after written design and implementation-plan review. Reuse existing local staging identities without resetting passwords or granting admin implicitly. Update docs/gallery only from verified current screens. No production routing changes or APK publication in this scope.

## Approved screen composition (2026-10-20)

- Map: full-height native map beneath a compact branded top area, reachable recenter action and attribution, persistent native destination navigation, and Report here as the main action. A compact legend explains data distinctions without instruction paragraphs. Selected observation opens a bottom sheet and a visible marker selection ring.
- Location picker: centre pin, concise selected-place/accuracy summary, Use current location and Confirm location. Back cancels location selection without discarding the draft.
- Report form: compact location summary first, category-specific input with units, optional attachment/note section, then Review report. Explicit condition choice. Keyboard-aware scrolling and48dp targets.
- Review: readable summary rows with Edit actions, one Submit action, and clear busy/retry feedback. Success shows Pending review and View my report.
- My reports: compact list with type, time and textual moderation status. Owner detail keeps full private evidence separate from public map data.
- Account: branded identity header and verification status, sign-in/create-account or signed-in actions, with secondary product details. Authentik pages match the owned logo, green/white system and concise account-task language.

Owner approved this structure with “Ya good use this”. This confirms the design direction; no product UI code has been changed for the redesign. The separate verification-email template defect has a source/local correction and passing regression test.

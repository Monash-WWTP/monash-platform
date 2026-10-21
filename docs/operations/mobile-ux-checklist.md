# CitizenFlood mobile UX resolution checklist

Updated21October2026. Scope: local staging debug app and source; production provisioning/release is separate. Samsung checks resumed after the user unlocked the device; only the specific checks recorded below are complete.

## Implemented

- [x] Map first with Map, My reports and Account navigation.
- [x] Floating + menu with four labeled report types, Back/outside dismissal and reduced-motion support.
- [x] Remove community banner and shorten Account wording; keep secondary information collapsed.
- [x] Fix Android OIDC return-to-app; separate synthetic account registration, email verification, login and photo-report submission exercised on Samsung.
- [x] Branded local identity/email templates with distinct confirmation/recovery actions and compact logo.
- [x] Replace wide map count card with compact count/list and refresh controls.
- [x] Add native accessible observation list: category, reading, ownership/approximate-location context and timestamp where supplied; selecting opens shared report details.
- [x] Dismiss observation list and private detail routes on account change; discard stale choices. Widget regression covers opening details and account-change dismissal.
- [x] Cache generated marker images and load them once per native controller; camera-only updates no longer rebuild symbols.
- [x] Compact location panel: point/source, coordinates/accuracy, current-location action and Confirm location. Keep more viewport available to the map.
- [x] Preserve explicit condition choice, immutable review, pending status, owner history, idempotent retry/media reuse and logout privacy fences.
- [x] Align CI with MapLibre’s Java21 requirement.

## Needs definition or service selection

- [x] Replace ambiguous new-report meanings with the approved versioned citizen protocol. The evidence review now recommends a versioned observation protocol rather than defining unsupported thresholds. See [metrics review](../science/CITIZEN_OBSERVATION_METRICS_REVIEW.md) and [approved design](../superpowers/specs/2026-10-21-citizen-observation-protocol.md). The implementation uses observable event responses and optional measurements with required context; historical records retain legacy meanings. Field validation remains pending.
- [ ] Place-name recognition/search: no approved geocoder is configured. Current map labels, center pin, current location and coordinates remain available. This needs provider/coverage/privacy selection before implementation.
- [ ] Validate first-use discovery of the approved icon-only + button with a new user. Keep the current tooltip and labeled menu; add a Report label only if observation shows hesitation.

## Verification and release gates

- [ ] Physical TalkBack traversal, reading order and map-list usability.
- [ ] Physical landscape/keyboard, denied permissions, offline/background/resume checks.
- [ ] Release/profile performance measurement; source optimization is not measured performance acceptance.
- [x] Latest debug APK rebuilt and installed on Samsung.
- [x] Confirm compact controls, observation list/detail and location picker in portrait/landscape on Samsung; numeric keyboard inspected.
- [ ] Production identity/backend/SMTP/storage configuration and acceptance; public signed APK remains unchanged.

Operator first-time MFA configure/resume friction belongs to the separate dashboard/identity follow-up, not this mobile checklist. Local dashboard password/TOTP callback succeeded; ungranted admin access returned403. The human-facing dashboard application name is already corrected in source; live provisioning must apply it.

See [original follow-up audit](../audits/2026-10-20-mobile-follow-up.md) and [Samsung evidence](samsung-mobile-acceptance-2026-10-20.md). Checkmarks record implemented source or the specific historical test stated; they do not imply the unchecked device/release gates passed.

Verification for this checklist pass:43Flutter tests passed, analyzer clean, debug APK built and installed. Repository policy passed421files; source inventory verified207pinned files. No production service or public APK was changed.

Protocol implementation verification:50 Flutter tests, clean analyzer, debug APK installed;199 Python tests passed/1skipped;45 dashboard tests and build passed. Samsung Rain/Unsure submission preserved Unknown and Pending status alongside the unchanged legacy report. Temperature context form visually inspected. See the21October addendum in Samsung evidence for the precise scope and remaining gates.

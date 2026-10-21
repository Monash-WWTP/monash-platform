# CitizenFlood mobile UX resolution checklist

Updated21October2026. Scope: local staging debug app and source; production provisioning/release is separate. The user elected source and existing screenshot review, so physical checks remain open.

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

- [ ] Confirm the water-level reference, rainfall interval and citizen criteria for Normal/Warning/Critical. The evidence review now recommends a versioned observation protocol rather than defining unsupported thresholds. See [metrics review](../science/CITIZEN_OBSERVATION_METRICS_REVIEW.md) and [proposed design](../superpowers/specs/2026-10-21-citizen-observation-protocol.md). Existing semantics remain unchanged pending design review and coordinated API/client implementation.
- [ ] Place-name recognition/search: no approved geocoder is configured. Current map labels, center pin, current location and coordinates remain available. This needs provider/coverage/privacy selection before implementation.
- [ ] Validate first-use discovery of the approved icon-only + button with a new user. Keep the current tooltip and labeled menu; add a Report label only if observation shows hesitation.

## Verification and release gates

- [ ] Physical TalkBack traversal, reading order and map-list usability.
- [ ] Physical landscape/keyboard, denied permissions, offline/background/resume checks.
- [ ] Release/profile performance measurement; source optimization is not measured performance acceptance.
- [x] Latest debug APK rebuilt and installed on Samsung.
- [ ] Confirm final compact controls physically when device review resumes.
- [ ] Production identity/backend/SMTP/storage configuration and acceptance; public signed APK remains unchanged.

Operator first-time MFA configure/resume friction belongs to the separate dashboard/identity follow-up, not this mobile checklist. Local dashboard password/TOTP callback succeeded; ungranted admin access returned403. The human-facing dashboard application name is already corrected in source; live provisioning must apply it.

See [original follow-up audit](../audits/2026-10-20-mobile-follow-up.md) and [Samsung evidence](samsung-mobile-acceptance-2026-10-20.md). Checkmarks record implemented source or the specific historical test stated; they do not imply the unchecked device/release gates passed.

Verification for this checklist pass:43Flutter tests passed, analyzer clean, debug APK built and installed. Repository policy passed421files; source inventory verified207pinned files. No production service or public APK was changed.

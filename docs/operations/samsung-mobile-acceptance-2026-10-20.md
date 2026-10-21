# CitizenFlood Samsung verification — 20 October 2026

This is local staging evidence for the map-first redesign, not production acceptance or a public APK release. Device: Samsung SM-A076B, Android16, USB debugging. Flutter3.44.7 builds the staging debug package `au.edu.monash.citizenflood.staging`. API8181 and identity9100 are accessed through USB reverse mappings; all services remain loopback-bound.

## Verified

- Native MapLibre renders the shared OpenFreeMap Liberty style in2D. Location picker shows a center pin and explicit coordinates; confirming carries the exact selected point into the form and review. Map navigation, compact category rows, condition selection, review and account screens were inspected on the device.
- The identity service successfully authenticated the existing development user but Android lost the authorization callback state. Logcat reported `No stored state - unable to handle response`. Removing the generated empty MainActivity `android:taskAffinity` fixed return-to-app; the verified account then rendered in CitizenFlood. The AppAuth package documents this exact configuration issue. A manifest regression test guards it.
- A separate synthetic account was created through public enrollment and verified using the local Mailpit message. Confirmation uses **Confirm your email**, not password-reset copy. That account then signed in through the Samsung browser and returned to the app as a verified session.
- On the Samsung, a synthetic plant-condition report was created at a selected map point with explicit Warning condition, a marked `QA_ONLY_SYNTHETIC_DO_NOT_PUBLISH` note and the app icon as a synthetic photo. Review displayed the chosen condition, point, observation time, note and photo. Upload/submission succeeded, showed Pending review and opened the existing My reports tab with the new Pending record. The test record was not approved or published.
- Identity branding uses the owned mark, green/light theme and short Sign in heading. The logo is constrained to56px itself, preventing its previous overlap with the form heading. The map's community-observation banner is removed; privacy context stays in observation details. Account copy is shortened and secondary information collapsed.
- Automated tests cover explicit condition selection, immutable reviewed payload, upload reuse and idempotency on uncertain retry, owner-only review reasons, private/public projections, identity-change fencing, logout dismissal of overlapping marker choices, delayed GPS results after account changes, existing-tab report refresh, Android Back after success, account errors and narrow layouts at200% text.

## Floating report menu refinement

The user approved a green + button opening four labeled report types: Rainfall, Water level, Temperature and Plant condition. Choosing one opens the location picker and then its form. Native popup dismissal supports Back and outside taps. Automated interaction and200% text/reduced-motion tests pass. On the Samsung, all four menu choices rendered and Rainfall opened the location picker then the Rainfall form after confirmation. Initial placement overlapped navigation; the corrected APK was installed and confirmed with the menu above the button and all four labels visible, leaving the bottom navigation clear.

## Independent review and resolution

One whole-change review found four important issues: overlap chooser data surviving account change, delayed GPS restoring a private camera location, Back returning to a submitted draft, and stale same-account report history. All were reproduced with failing tests and corrected in one pass. A minor visual finding about identical owner/public markers was promoted because it could imply public approximate points were precise; owner markers are filled and community markers outlined. The marker-key regression failed before the correction and passes afterward. No second review round was run.

The combined Sign in / Create account entry intentionally opens the supported OIDC provider page, where Sign up is available. The installed authentik does not support a direct `prompt=create` enrollment shortcut. This costs one extra provider-page action while preserving the authorization context and PKCE flow.

## Remaining acceptance

Production hosting, production email delivery/storage, production identity URLs, signing custody and public release remain pending. Local testing does not qualify them. Full physical TalkBack, landscape/large-font coverage, permission-denied camera/location, offline/background-resume, profile/release performance, recovery completion and local admin moderation are still acceptance work; widget and API tests do not replace those device journeys. Current debug timings do not establish release performance.

Source: [Flutter AppAuth troubleshooting](https://pub.dev/packages/flutter_appauth#troubleshooting), installed package README, local identity/API logs and Samsung UI inspection. No credentials, tokens or verification links are included here.

## Verification commands

Final source checks: Flutter41tests passed; analyzer reported no issues; staging debug APK built. `uv run --locked pytest tests services/api/tests -q` passed194tests with1skipped against the guarded disposable database on5433. The imported source inventory verified207pinned files. Repository policy passed419files before this document’s final edits. API OpenAPI is regenerated for the additive owner review-reason field. These results are software verification, not the remaining acceptance gates above.

## Scientific observation protocol — 21 October 2026

The rebuilt local API advertises citizen-observation revision1. The latest debug APK was rebuilt and installed on the same Samsung. The map loaded the existing legacy record; the new menu displayed Flooding, Rain, Water appearance and Add measurement. A selected-point Rain report with Unsure was reviewed as Unknown with visual method, time and location, then submitted successfully. My reports displayed the new Pending Rain/Unknown record alongside the unchanged legacy Wastewater plant/Warning record. This synthetic record belongs to the development QA account and must remain unpublished. The temperature form was visually inspected: subject, value/unit, instrument, sampling context and explicit unknown calibration were visible; no temperature reading was submitted.

The device run found that the map requested200 mixed history records while the initial v2 endpoint allowed100. The bound now matches the existing500 maximum; a failing regression was corrected and the rebuilt API restored map loading.

Final software verification:50 Flutter tests passed; analyzer clean; staging debug APK built and installed;199 Python tests passed with1skipped against the disposable5433 test database;45 dashboard tests and production build passed; repository policy437files and pinned inventory207files passed before final documentation edits. One fresh review found retry identity, account fencing and capability retry issues; all three were reproduced and fixed with regression tests.

The earlier photo/enrollment checks remain historical evidence, not a new-protocol photo test. Full physical TalkBack, new-protocol permission/offline/background/account-switch journeys, field comprehension/reference validation and production services remain open. The public signed APK is unchanged.

## Revision2 context/update verification — 21 October 2026

Source adds optional flooding movement, private camera/gallery provenance and linked updates from existing owned flooding detail. Local API was rebuilt and advertises supported revisions1/2; staging debug APK was rebuilt and installed. Automated checks:201 Python tests passed with1skipped;53 Flutter tests passed;46 dashboard tests passed; analyzer clean; dashboard/debug APK builds passed. An initial stale OpenAPI snapshot failure was resolved by regeneration before the final green suite. Repository policy440files and pinned inventory207files passed before final documentation additions.

One fresh review of this extension reported no concrete Critical/Important/Minor findings. Device inspection found the Samsung locked; the new revision2 original/update submission has not yet been physically verified. Earlier revision1 Samsung evidence remains historical and is not counted as revision2 acceptance. Full physical accessibility, failure-path, field-validation and production gates remain open. Synthetic records must remain unpublished.

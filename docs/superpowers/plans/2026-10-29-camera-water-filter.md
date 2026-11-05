# Camera Water Filter Implementation Plan — executed inline

Approved scope: direct live-camera water effect without ARCore or an explanatory banner.

- [x] Native Camera2 activity and GLES compositor, separate from tracked AR and the synthetic 3D preview.
- [x] Main toolbar entry works without an account, API, observation or report payload; retain depth-preview entry.
- [x] Coverage slider/drag, tap/Ripple, Pause/Play, Reset and Close.
- [x] Camera permission/error recovery, background camera release and account/launch-token invalidation.
- [x] Reuse extracted Evan GPU simulation where supported, with analytic compatibility normals when unavailable.
- [x] Rotation/crop and framebuffer-budget tests; launch/no-payload/account-invalidation tests.
- [x] Independent review; guard GPU commands, reject unchanged float fields and remove rate-switch backlog.
- [x] Local tests, analysis, staging APK and repository checks; emulator camera/controls/background checks.
- [ ] Physical Samsung camera orientation, permissions/contention, large text and sustained heat/frame-pacing acceptance.
- [ ] Native floating-point GPU execution and tracked AR acceptance on supported physical hardware.

See `docs/operations/camera-water-filter.md` for actual evidence and limitations. No sensor assistance, segmentation, recording or report mutation is implemented.

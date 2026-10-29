# Camera water filter without ARCore — approved implementation scope

## Intent

The user and supervisor are exploring a Snapchat-style water effect over the live rear camera without requiring ARCore. This is a new camera-filter mode alongside the existing synthetic 3D preview and tracked AR mode. The user requested implementation and explicitly removed the explanatory banner requirement. Production acceptance remains separate.

## Approaches

1. Recommended first release: live camera compositing with manually positioned water, adjustable apparent horizon/perspective and optional rotation-sensor assistance. Broad compatibility; no claim of world anchoring or metre-accurate placement.
2. Marker tracking: a known-size printed marker could provide scale/pose, with setup burden and loss when the marker leaves view. Separate later work.
3. Alternative world tracking/ML scene estimation: potentially better placement, but adds device, model, SDK/license and validation requirements. Not a shortcut to guaranteed metric tracking. Separate research phase.

## Proposed experience

Offer a direct “Camera water” toolbar action independent of backend/accounts and a report-preview entry, separately from “AR preview” and “3D water preview”. Request camera permission only on entry. Start with a live rear-camera view and animated water covering a user-adjustable lower portion. Drag the apparent water line, adjust perspective/coverage, and use Ripple, Pause, Reset and Close. Put secondary visual controls in one expandable panel. Optional rotation assistance must be switchable and enabled only when sensors are available and tested; it cannot compensate for walking or recover translation/scale.

Retain the entered report depth as context without implying the manual overlay represents that many metres in the scene. Controls describe appearance/coverage, not measured depth. Per the user, do not add an explanatory banner. Use a distinct “Camera water” action, immediate live effect, native Ripple/Pause/Reset/Close controls and a coverage slider. Do not silently substitute it for tracked AR. Do not claim water hides behind real objects correctly.

## Rendering and safety of data

Prefer a native camera texture + GLES compositor, adapting the existing GPU wave solver and optics. Use platform Camera2 with a SurfaceTexture and GLES compositor; no new SDK dependency. Do not open ARCore or introduce another tracking SDK for this first mode. Camera imagery supplies screen-space refraction; sky reflection is synthetic unless a validated environment source exists. No virtual pool walls/floor are placed over the feed. Existing 3D caustics cannot be projected accurately onto unknown real geometry.

No camera capture, upload, microphone, location or report mutation in this mode. Do not attach synthetic filtered views as observation evidence. Stop/release camera and GPU resources on background/close; preserve account invalidation. Permission denial, camera contention and graphics failure must leave a usable Close/return path. Keep the existing report-photo path unchanged.

## Acceptance

Run on the actual Samsung without ARCore installed/enabled. Verify camera startup, correct orientation/crop, overlay controls, pause/reset, background/resume, permission denial/revocation and camera contention. Measure frame pacing and heat over a sustained phone run, rather than borrowing browser/emulator FPS. Test large text, rotation and sensor absence. Retain normal reporting and do not change submitted observations. Synthetic 3D preview remains the fallback if live camera rendering is unavailable.

## Agreed implementation boundary

The current request is a camera effect without ARCore. It composites waves and camera-image reflection/refraction with adjustable coverage. It does not implement Snapchat's proprietary tracking stack or world anchoring. Keep the entered research observation unchanged; camera-filter settings are presentation state only.

Implementation uses a native Camera2 compositor with a bounded framebuffer and an emulator compatibility path. See docs/operations/camera-water-filter.md for the observed native float-target driver failure and physical-device qualification gates.

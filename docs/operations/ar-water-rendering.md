# Android AR water rendering refinement

Implement Evan Wallace's heightfield approach on Android: a bounded damped ripple grid, computed normals, camera-feed refraction and angle-dependent surface reflections. Use a portable CPU grid rather than assuming renderable floating-point textures on every GLES2 phone. Preserve the ARCore anchor, reported mean depth, 3m footprint, ruler, tracking-loss suppression and current depth occlusion. Ripples are decorative and must never change the recorded reading.

Camera-feed refraction is a screen-space approximation; a single camera cannot reveal hidden scene content or provide true surrounding reflections. Use explicitly synthetic sky lighting for missing reflections. No virtual pool, sphere or invented underwater objects belong in the reporting overlay. These differ from the browser pool demonstration intentionally. No camera/depth images leave the device.

Reference: Evan Wallace, WebGL Water, https://github.com/evanw/webgl-water (Copyright2011EvanWallace, MIT). Native port retains attribution. Physical AR visual/performance acceptance remains required on supported hardware.

## Verification

- Native unit tests: six passing (ripple propagation/bounds/reset and depth input).
- Flutter: 66 tests passing; static analysis reports no issues.
- Debug staging APK builds successfully.
- Repository policy and pinned-source manifest checks pass.
- Read-only code review found a coordinate-basis error in refraction; the renderer now transforms ripple perturbations into camera axes before offsetting screen UV.

These checks do not validate the runtime GLES shader or visual quality. The available Samsung does not support ARCore. The API 36 emulator exposes camera ID 10 while the installed ARCore requests camera ID 0, so AR session startup fails before rendering. Supported-device acceptance must still check shader startup, anchoring, ripple edges, depth occlusion, orientation changes, frame rate, heat and camera responsiveness.

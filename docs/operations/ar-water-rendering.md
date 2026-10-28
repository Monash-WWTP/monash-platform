# Android AR water rendering refinement

Implement Evan Wallace's heightfield approach on Android: a bounded damped ripple grid, computed normals, camera-feed refraction and angle-dependent surface reflections. Use a portable CPU grid rather than assuming renderable floating-point textures on every GLES2 phone. Preserve the ARCore anchor, reported mean depth, 3m footprint, ruler, tracking-loss suppression and current depth occlusion. Ripples are decorative and must never change the recorded reading.

Camera-feed refraction is a screen-space approximation; a single camera cannot reveal hidden scene content or provide true surrounding reflections. Use explicitly synthetic sky lighting for missing reflections. No virtual pool, sphere or invented underwater objects belong in the reporting overlay. These differ from the browser pool demonstration intentionally. No camera/depth images leave the device.

Reference: Evan Wallace, WebGL Water, https://github.com/evanw/webgl-water (Copyright2011EvanWallace, MIT). Native port retains attribution. Physical AR visual/performance acceptance remains required on supported hardware.

## Verification

- Native unit tests: nine passing (ripple propagation/bounds/reset, depth input and bounded/visible orbit framing).
- Flutter: 67 tests passing; static analysis reports no issues.
- Debug staging APK builds successfully.
- Repository policy and pinned-source manifest checks pass.
- Read-only code review found a coordinate-basis error in refraction; the renderer now transforms ripple perturbations into camera axes before offsetting screen UV.

The camera-free variant has now been exercised in the emulator; the AR camera-feed shader path and physical visual quality remain unverified. The available Samsung does not support ARCore. The API 36 emulator exposes camera ID 10 while the installed ARCore requests camera ID 0, so AR session startup fails before rendering. Supported-device acceptance must still check shader startup, anchoring, ripple edges, depth occlusion, orientation changes, frame rate, heat and camera responsiveness.


## Camera-free 3D fallback

The depth preview screen offers a separate **3D water preview** on Android, including devices without ARCore. A standalone native activity uses the same renderer, heightfield and surface shading with an orbit camera and synthetic gridded floor. It never starts an ARCore session or requests camera permission. Refraction is evaluated against the synthetic floor; it cannot validate camera-feed refraction or real-world depth occlusion. It has no capture/upload or report mutation path.

Drag to orbit and pinch to zoom; accessible button alternatives are under **View controls**. **Ripple** adds a disturbance; **Pause/Play** controls time; **Reset** restores camera, simulation and playback. Pitch/zoom are bounded above the surface. For numerical/rendering bounds, the standalone scene accepts depths from 0 to 1000 m; larger entries receive a preview-only error and are unchanged. Zero depth shows the dry reference floor. Activity and launch-token lifecycle preserve existing account invalidation behavior.


### Fallback acceptance — 2026-10-28

API 36 x86_64 emulator (Monash_AR_QA), debug staging APK:

- Launched the native 3D scene with `com.google.ar.core` disabled and camera permission denied. No installation/permission prompt or water GL error was logged.
- Visible gridded-floor refraction, water surface and external depth scale; synthetic 0.5 m draft reference retained. Review's hidden ruler was reproduced in the first render and corrected with an explicit scale overlay beside the patch.
- Ripple, Play/Pause, drag orbit, zoom button and Reset exercised. Paused scene pixels were identical between two captures (system chrome excluded).
- Landscape at font scale 1.5 retains a rendered scene and scrollable controls, including Close. Restored portrait/font scale 1.0 afterward.
- Large-depth visibility regression test verifies scene footprint/distance ratio across 0, 0.5, 10, 100 and 1000 m. The synthetic scene widens its unlabelled footprint as depth increases; the AR footprint stays 3 m. This keeps the water inspectable without changing the displayed/reported depth.
- Pinch uses Android's standard scale gesture detector; physical touch feel, frame rate and heat still require phone testing. The available Samsung was disconnected for this check.

The fallback proves native mesh/shader rendering without ARCore. It does not establish real-world tracking, camera refraction, depth occlusion or AR performance acceptance.

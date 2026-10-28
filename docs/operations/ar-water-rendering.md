# Android water rendering

## Full camera-free preview

**3D water preview** now runs bundled Evan Wallace WebGL Water / lightgl.js source in an isolated Android WebView. It uses the actual GPU heightfield solver, two-sided ray-traced pool reflection/refraction, caustics, analytic ambient occlusion and pool-rim shadows. It is live rendering, not footage. Above/Underwater controls, tap ripples, drag orbit and pinch/button zoom work within the synthetic scene. No sphere is invented in the reporting view.

Source: `apps/citizenflood/android/app/src/main/assets/water/vendor/`, pinned upstream commit `73eda8be832b649367b25ea5690c1f0181bb56ad`. `UPSTREAM.json` records original and bundled SHA-256 values. `lightgl.js` and `cubemap.js` are unchanged; `water.js` and `renderer.js` have documented mobile/depth/numeric adaptations. MIT copyright headers and full license are packaged. The original tile/sky photographs are not bundled: `textures.js` creates project-owned procedural textures locally. Source provenance tests run in CI.

The pool's bottom is `depthM / worldScaleM` below the mean surface, with `worldScaleM=(3+depthM)/2`, preserving the entered vertical distance while widening the unlabelled synthetic footprint for inspectability. Zero depth is dry. Decorative waves are bounded to at most 2.5 cm and 20% of depth. The reported value is never modified. The pool, lighting and underwater view are illustrations, not reconstruction, measurement or evidence.

Mobile bounds: 128² simulation, initially 128-detail water mesh, 512² caustic map, at most 800,000 canvas pixels and device pixel ratio 1.5. Measured low rendered-frame rates reduce canvas/mesh/caustic work in two stages (400k/96/256 then 200k/64/128), retaining full shader features. Sustained <15 FPS at the minimum stage switches to the labelled basic preview. The governor ignores paused/background time. A 60 Hz elapsed-time clock caps catch-up at three ticks; animation stops when backgrounded. Context loss, renderer failure, missing WebView, unavailable extensions/FBO or 15-second startup timeout also select basic graphics. Users may select Basic/Full graphics under View controls.

The WebView loads only exact allowlisted bundled resources under `https://water.citizenflood.invalid`. Network, navigation, file/content access, mixed content, storage and permission requests are blocked. There is no JavascriptInterface. Only depth crosses into the page; reference/context remain native. Native commands are fixed and JS-validated. Account invalidation closes/destroys either renderer. WebView DevTools are enabled only in debuggable APKs.

## Native AR and basic compatibility renderer

The real-camera AR overlay and Basic graphics use a native adaptation of Evan Wallace's heightfield approach: a bounded damped ripple grid, computed normals, camera-feed refraction and angle-dependent surface reflections. Use a portable CPU grid rather than assuming renderable floating-point textures on every GLES2 phone. Preserve the ARCore anchor, reported mean depth, 3m footprint, ruler, tracking-loss suppression and current depth occlusion. Ripples are decorative and must never change the recorded reading.

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

The depth preview screen offers a separate **3D water preview** on Android, including devices without ARCore. The basic compatibility scene uses the native AR renderer, heightfield and surface shading with an orbit camera and synthetic gridded floor. It never starts an ARCore session or requests camera permission. Refraction is evaluated against the synthetic floor; it cannot validate camera-feed refraction or real-world depth occlusion. It has no capture/upload or report mutation path.

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


## Full renderer verification — 2026-10-28

- Browser: live above/underwater rendering, zero depth (dry), 1000 m normalization, no GL error. Software SwiftShader measured roughly 7 FPS at initial quality and roughly 34 FPS after adaptive reduction; this is environment-specific, not a phone benchmark.
- Actual Android WebView: full effect loaded from bundled assets with ARCore disabled and camera denied. Initial pre-governor emulator samples were 56.6–60 FPS, falling with competing software-browser load. Final-build acceptance is recorded below.
- GPU readback regression: flat caustic footprint at 0.5 m was incorrectly centred at (82.5,54) on a 128² target before the depth-offset fix; it is correctly (64,64) afterward. A grazing underwater ray produces a valid reflected pixel and GL_NO_ERROR. Explicit total-internal-reflection guarding avoids evaluating a zero refracted ray; this driver produced a nonblack pixel even before that defensive fix.
- Fresh review found the caustic offset and underwater zero-ray issues; both corrected. Pure JS tests exercise depth normalization, dry state, bounded pixels, clock catch-up, command allowlist, quality governor and source provenance. Native tests exercise exact asset origin/paths and existing depth/ripple/orbit logic.

### Reproduce shader checks in a debug Android WebView

The debug APK enables standard Android WebView DevTools; release builds do not. With the 3D preview open, find `webview_devtools_remote_<app-pid>` using `adb shell cat /proc/net/unix`, forward it to loopback TCP 9223, then run:

```sh
node apps/citizenflood/test/water/android-webview-check.cjs --file apps/citizenflood/test/water/gpu-check.js
```

The tool targets only the synthetic local water origin and reads the actual shader output. It backgrounds/resets the decorative scene; no report is submitted or changed. Use the standard `WEBGL_lose_context` extension through the debug inspector to verify native basic failover. Remove the adb TCP forward when finished.

### Release gates

The emulator does not establish phone touch quality, frame pacing, heat, battery, memory stability or ARCore anchoring/occlusion. A connected physical phone must still complete sustained above/underwater use, background/resume/rotation and fallback tests. A supported ARCore phone must separately validate the camera overlay; its hidden-scene/reflection limits remain unchanged. This work produces a debug staging APK and an unmerged PR, not production release approval.


### Final Android WebView acceptance

Debug staging APK, API 36 emulator, ARCore disabled and camera denied:

- Actual shader readback: caustic centre (256,256) on a 512² target, grazing total-internal-reflection pixel (31,89,100,255), GL_NO_ERROR.
- Rendered-frame governor samples at initial quality ranged from approximately 43–60 FPS in this environment, with later samples 59–60 FPS. These are animation-frame delivery measurements, not GPU timing or physical-phone results.
- Pause: identical canvas pixels between captures. Explicit network and file fetch probes are rejected. GPU shader readback runs through the debug inspector without a native JavaScript bridge.
- Injected WebGL context loss: scene stops, native view switches to labelled Basic graphics, normal report context and Close remain available; Full graphics retries successfully.
- Injected WebView renderer-process crash (`Page.crash`): DevTools reports Render process gone; the app stays alive in labelled Basic graphics and can retry Full graphics.
- Pure checks: 67 Flutter tests, ten native unit tests, six Node tests, static analysis, debug build, repository policy and pinned-source manifest pass. No original photograph assets or video footage are used.

Startup timeout, missing WebView/provider and unsupported real-device extension combinations are implemented but not all independently injected here. Physical phone thermal/battery/long-run performance and real-camera AR acceptance remain open.

- Final full-renderer rotation check: landscape at font scale 1.5 retains the scene and scrollable Close/control access; portrait/font scale restored. Home stops WaterPreview frame-stat logging; selecting CitizenFlood from Recents resumes the native scene with unchanged 0.5 m/floor context. Native shader readback, failure injection and recording used the same final APK. A synthetic above/underwater recording was captured locally; it is not attached to a report.

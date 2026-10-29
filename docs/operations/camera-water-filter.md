# Camera water

The main-screen camera icon opens a live rear-camera water effect without ARCore, sign-in, an observation or an API connection. It is also available from the depth-preview screen. The user requested no explanatory banner; the camera opens directly with a coverage slider and Ripple, Pause/Play, Reset and Close. Dragging also changes coverage, and tapping disturbs the water. Pause affects water animation while the camera remains live.

This is native Camera2 → SurfaceTexture → GLES compositing, not the proprietary Snapchat SDK. Camera imagery supplies the filter's screen-space distortion and mirrored reflection. There is no world tracking, segmentation, metric height placement or invented pool geometry. No observation data crosses the camera launch channel; coverage settings never change research readings. The mode has no photo/video recording, microphone, location or upload path. Existing report photos are unchanged.

Camera permission is requested only on entry. Camera devices/sessions/output surfaces and the background handler are closed on background/close. Native launch tokens and the home shell's account-generation listener close previews on account changes. Permission denial, camera contention and graphics errors retain Retry/Close. Rear-camera buffers are bounded to a supported size at or below 1280×720 when available; the compositor framebuffer is capped at 800,000 pixels with aspect-preserving crop. Sensor/display rotation follows Android Camera2 metadata; physical orientation acceptance still requires a phone.

## Rendering paths

Supported physical devices prefer GLES3 with sized RGBA32F/RGBA16F ping-pong fields and core half-float types. GLES2 texture extensions remain supported. The native solver shaders are generated from the pinned Evan Wallace source by `scripts/export_native_water_shaders.cjs`; CI checks that extraction. Native GPU startup checks require positive perturbed height and negative update velocity, not an unchanged zero field. Native GPU and CPU clocks drop elapsed time when switching modes; the regression test covers a long GPU session. Ripple/Reset and frame updates share guarded GPU failure handling.

When native floating-point rendering is unavailable, the camera compositor uses lighter analytic animated normals. Native AR/basic graphics retain their CPU mesh fallback. VBOs support both GLES2 and GLES3; AR occlusion bytes use portable RGBA8 (low byte R, high byte A), with a strided-byte packing regression test. Real-camera AR keeps its own anchor/matrices/depth path and remains separately qualified; the camera filter does not pretend to provide that tracking.

### Emulator driver limitation

The API 36 Gfxstream emulator rejected unsized full/half float FBOs. Enabling the native sized-float GLES3 path terminated the *emulator host* with SIGSEGV/exit 139 under both host and SwiftShader modes. Ranchu/goldfish emulators therefore explicitly use GLES2 compatibility graphics and skip native float targets; the policy has a regression test. This does not disable the existing WebView GPU 3D demo, which uses a different graphics path. Native floating-point execution, vertex displacement and AR optics must still be verified on a physical supported phone; source/build tests cannot substitute for that.

## Verification commands

```sh
cd apps/citizenflood
flutter analyze
flutter test
node --test test/water/*.test.cjs
cd android
./gradlew :app:testDebugUnitTest
```

Build the debug staging APK using the app README. Real-device acceptance: live camera orientation/crop, coverage/ripple/pause/reset, denied/revoked permission, camera contention, background/resume, rotation/large text, sustained frame pacing, heat/battery and normal report-photo recovery. ARCore is unnecessary for this camera mode. A different ARCore-compatible device is still needed for tracked AR acceptance.

Implementation reference: [Android Camera2 preview](https://developer.android.com/media/camera/camera2/camera-preview). No extra camera SDK dependency or remote code is introduced.

## 2026-10-29 camera-filter acceptance

API 36 emulator, ARCore disabled: direct toolbar launch displays the live virtual rear camera without an account/API/report. Compatibility compositor samples approximately 60 rendered frames/s and 30 consumed camera frames/s at 625×1279; these are delivery counts, not physical GPU timings. Pause changes to Play; ripple, drag/coverage, reset and close were exercised. Backgrounding disconnects the camera (no active CameraService client); Recents resumes it. Closing returns to the app. Local demo: `/tmp/camera-water-demo.mp4`.

69 Flutter tests, 18 native unit tests and seven Node tests pass (94 total), alongside static analysis, staging debug build, shader extraction, repository policy and pinned-source inventory checks. Physical orientation/thermal/performance, denied/revoked permission and camera contention remain acceptance gates.

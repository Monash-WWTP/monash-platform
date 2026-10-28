# Full water rendering in the Android preview

The user asked to complete the visual upgrade after being told the native approximation does not match Evan Wallace's demo or establish production readiness. Implement the actual MIT WebGL Water simulation and surface/caustic shaders offline in Android's camera-free preview. Preserve its entered depth and private context. Physical-device release acceptance remains required; never claim production readiness from the emulator.

## Approach

Use bundled WebGL source inside a restricted Android WebView, with existing native controls. This directly reuses Evan's GPU simulation, ray intersections, two-sided reflection/refraction, caustics, ambient occlusion and pool-rim shadows. Keep the existing camera-free Kotlin renderer as a clearly labelled basic compatibility fallback. A second native reimplementation would add divergence and more unverified shader work; footage would not respond to touch or view changes. No remote code or original third-party image assets are used. Bundle project-owned procedural tile/sky textures and full MIT notices with pinned provenance.

The synthetic pool is an illustrative scene; its normalized bottom follows the entered depth relative to its synthetic width, with bounded decorative disturbances. Zero depth is dry. It is not a reconstruction or a measurement. Above/Underwater controls show both sides; no hidden real-world objects are invented in the AR camera overlay. The full pool rendering does not replace ARCore tracking or camera-only approximation limits.

## Runtime requirements

Only allowlisted bundled assets may load, under a synthetic HTTPS origin. Disable file/content access, navigation, network loads, storage and native JavaScript bridges. Native controls send fixed allowlisted commands. Bound canvas resolution and mesh/caustic sizes for mobile, use elapsed-time simulation with a catch-up cap, pause rendering when backgrounded, destroy WebView/resources on close, handle context loss and renderer crashes with a clear basic fallback. Preserve launch-token/account invalidation and no capture/upload/report mutation.

## Acceptance

Source provenance/license checks and tests for depth normalization, zero/large values, simulation timing, pixel budget and asset origin allowlist. Test the bundled renderer in browser and actual Android WebView with ARCore disabled/camera denied; inspect above/underwater, moving caustics/refraction, pause/reset/orbit/zoom, background/resume, rotation and fallback. Record measured emulator frame timing without generalizing it to phones. Build/analyze/native/Flutter/repository checks; independent final review. Phone frame rate, thermal/battery behavior and real AR remain release gates.

# Water preview without ARCore

The user approved the recommended 3D preview fallback and asked to implement it. Give Android users a camera-free, touch-controlled water scene so unsupported phones can inspect the same ripple simulation and lighting used by the AR renderer. Preserve the report and its entered depth/reference.

## Approaches

- Selected: standalone 3D scene. Reuse native GLES water rendering and the ripple solver; orbit/zoom controls, ripple, pause and reset. Requires neither an ARCore session nor camera permission.
- Camera overlay: would show surroundings but cannot provide stable placement or occlusion without tracking; outside this request.
- Printed-marker tracking: needs a separate tracking implementation and physical marker; outside this request.

## Design

Add an explicit “3D water preview” action alongside the AR action. It is available on Android regardless of ARCore support. A native activity shows a bounded water surface at the entered depth above an illustrative gridded floor, a depth scale, a compact title and “Illustrative scene · not your location”. Drag rotates, pinch zooms; accessible buttons provide rotation/zoom as well. Ripple, Pause/Play, Reset and Close remain visible through rotation/insets and large text via scrolling controls. Start above water; orbit remains above the surface. Reset restores view, simulation and playback. No camera, location, network or report mutation is used. Account invalidation closes either preview through the existing launch-token mechanism.

Reuse the same heightfield, mesh and surface shading. Refraction in this scene samples an analytical synthetic floor rather than camera content; reflections remain synthetic. The developer will choose bounded orbit/zoom values and a neutral backdrop. Do not claim this validates real-world anchoring, occlusion or camera performance. No new dependency. Implementation bounds the synthetic preview to 0–1000 m, with an explicit preview-only error above this range. Its unlabelled synthetic floor widens with depth to keep the surface inspectable; the AR patch remains 3 m.

## Acceptance

Launch without ARCore or camera permission; see animated water; orbit, zoom, ripple, pause/resume/reset work; return preserves the report; invalid inputs and account invalidation stay protected. Build/tests plus emulator screenshots and GL error checks verify the standalone renderer. Physical AR acceptance remains separate.

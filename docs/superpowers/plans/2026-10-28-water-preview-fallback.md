# Water Preview Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Inspect native water on Android without ARCore.
**Architecture:** A separate Activity drives the existing renderer in standalone mode, sharing its ripple mesh and shader, with synthetic floor refraction and orbit controls. Flutter exposes a separate native launch method; close invalidates both activities.
**Tech Stack:** Flutter, Kotlin, GLES2; no new dependencies.
**Spec:** docs/superpowers/specs/2026-10-28-water-preview-fallback-design.md

## Global Constraints

No camera permission/session, uploads or report mutation in 3D mode. Preserve AR behavior. Label the scene as illustrative. Reuse ripple simulation. Keep launch-token account invalidation.

## Review Focus

- Unsupported ARCore: standalone must not request installation or camera.
- Zero/large reported depth: finite camera and scene remain visible.
- Rotation/large font: controls and scene remain reachable.
- Pause/background/reset: no simulation catch-up or lifecycle crash.
- Account invalidation: no private context remains in a native activity.

## Task 1: Native fallback and entry point

Files: DepthRenderer.kt, new WaterPreviewActivity.kt and PreviewOrbit.kt, MainActivity.kt, AndroidManifest.xml, Flutter depth_preview service/screen, corresponding tests.

- [x] Add failing Flutter tests: the 3D action sends open3d with unchanged depth/reference/context, remains available after AR failure, and closes on account change.
- [x] Add native orbit tests: clamp pitch/zoom, ignore nonfinite gestures, fit zero and 10m depths, reset restores defaults.
- [x] Observe failing tests, implement native activity, orbit state, renderer standalone mode and channel action.
- [x] Run native and Flutter tests, analysis, APK build and repository checks.
- [x] Install on emulator; inspect rendering/controls, pause/reset/orbit/zoom, lifecycle and GL logs without granting camera.
- [x] Review final diff with a fresh reviewer; fix important defects, document verification and commit/push PR update.


## Execution evidence

Observed red→green for the missing 3D action, orbit implementation and large-depth footprint regression. Final verification: 67 Flutter tests; nine native tests; Flutter analysis; debug APK; repository policy and 207-file pinned-source manifest. Fresh review found hidden scale and disappearing large-depth surface; both corrected. Emulator acceptance with ARCore disabled and camera denied is recorded in docs/operations/ar-water-rendering.md. Close/back returned to the unchanged synthetic floor/0.5 m draft. Physical-device touch/performance and AR acceptance remain pending.

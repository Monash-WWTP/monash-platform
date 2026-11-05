# Full Water Renderer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Run Evan Wallace's full GPU water effect offline in Android's 3D preview.
**Architecture:** Vendor source with provenance; adapt pool depth/quality and write mobile scene controller. A restricted WebView scene implements native preview commands; existing Kotlin GL renderer remains the explicit basic fallback.
**Tech Stack:** Kotlin, Android WebView/WebGL1, vendored MIT JavaScript; no remote content or new package dependency.
**Spec:** docs/superpowers/specs/2026-10-28-full-water-renderer-design.md

## Global Constraints

No camera/session/network/report mutation. Local asset allowlist, no JS native bridge. Entered depth retained, zero dry. Label fallback. Physical phone acceptance stays open.

## Review Focus

- Unsupported/failed GPU or missing WebView: usable basic preview/Close without loops.
- Asset traversal/navigation/foreign URL: never loads network or private app files.
- Background/context loss/close: animation and resources stop; safe recovery.
- Zero/huge depth and geometry: finite rays and consistent pool floor.
- Pause/orbit/underwater/control reset: responsive drawing without accidental time catch-up.

## Task 1: Offline full renderer

- [x] Add failing Node tests for pool normalization, fixed-step clock, pixel-budget and command validation; native tests for strict asset allowlist.
- [x] Vendor pinned MIT source and procedural assets; adapt source for normalized depth, resolution and numeric stability; add scene controller with touch and native commands.
- [x] Integrate restricted WebView and clearly labelled basic fallback with lifecycle handling; preserve existing close/token behavior.
- [x] Run pure/unit/widget tests and static analysis/APK build; exercise browser and emulator rendering, context loss, timing, lifecycle/fallback, depth and underwater view.
- [x] Fresh review, fix substantive defects, document exact provenance/acceptance, commit and push PR update without merging.


## Execution evidence

Observed failing tests for missing scene config/policy and quality governor, then six Node and ten native tests passing. Flutter 67 tests and analysis pass; debug staging APK builds. Repository and pinned-source checks pass. Browser and actual Android WebView shader readbacks pass caustic alignment and finite underwater reflection. Fresh review found depth-offset and TIR zero-ray defects, both corrected; caustic readback changed from off-centre failure to centred success. Android tests with ARCore disabled/camera denied verify pause, local asset isolation, context-loss fallback, renderer-process-crash fallback, Full retry, rotation/font scale 1.5, background/Recents resume and controls. Full initial-quality samples approximately 43–60 FPS in this emulator; physical phone frame pacing/heat/battery and real AR acceptance remain pending. Exact provenance, adaptations and runtime limits are documented in docs/operations/ar-water-rendering.md.

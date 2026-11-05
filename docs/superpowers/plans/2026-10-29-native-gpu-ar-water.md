# Native GPU AR Water Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for inline implementation and final independent review.

**Goal:** Port Evan's actual GPU wave/surface pipeline into the native AR renderer.
**Architecture:** GLES3 sized-float / GLES2 extension ping-pong height/velocity/normal field, native mesh vertex sampling and ray-based optics; existing CPU renderer is the capability/error fallback.
**Spec:** docs/superpowers/specs/2026-10-29-native-gpu-ar-water-design.md

- [x] Test bounded fixed-step timing and source provenance, then implement native GPU solver/shader extraction.
- [x] Integrate GPU displacement, peaking normals, refraction-ray projection and lighting with AR transforms; preserve reference/ruler/occlusion and reset.
- [ ] Validate float-FBO execution/readback, native standalone rendering, lifecycle/reset and CPU fallback; run native/Node/Flutter checks and APK build.
- [x] Independent review, address defects, record supported-device limitations, commit and update PR.

Review focus: GLES2 capability failures/state leakage; zero/shallow depth; context reset/tracking pause; below-water TIR; native non-AR validation must not be reported as real AR acceptance.

Build/unit/provenance checks pass. Native float execution/readback remains a physical-device gate: API 36 emulator hosts crashed under both host and SwiftShader GLES3; ranchu/goldfish now use tested GLES2 compatibility policy. Existing WebView GPU evidence is separate.

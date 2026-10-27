# Reported-depth AR Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Visualise a draft or owned report depth without altering observations.
**Architecture:** Flutter validates a reading and opens a private Kotlin Activity. ARCore anchors a bounded OpenGL water patch to a manually confirmed reference.
**Tech Stack:** Flutter, Kotlin, ARCore, OpenGL ES.
**Spec:** ../specs/2026-10-27-report-depth-ar-design.md

## Global Constraints
Local-only illustration, not measurement or forecast; no evidence uploads.
Require structured water_reading/depth/metres, finite nonnegative value and reference.
Normal reporting remains available without AR.

## Review Focus
Reject gauge stage; preserve draft; handle unsupported/denied camera; hide water on tracking loss; distinguish missing depth from active occlusion.

### Task 1: Flutter integration
- [x] Write failing tests for eligibility, channel payload and fallback UI.
- [x] Implement services/depth_preview.dart and screens/depth_preview_screen.dart.
- [x] Wire widgets/measurement_fields.dart and widgets/report_detail_sheet.dart.
- [x] Run Flutter tests and analyzer.

### Task 2: Native AR
- [x] Test native argument validation in android/app/src/test.
- [x] Add private ar/DepthPreviewActivity.kt, ar/DepthRenderer.kt and method channel.
- [x] Configure optional ARCore, permission, installation and lifecycle handling.
- [x] Render camera, horizontal hit-test confirmation, bounded water, ruler and optional depth occlusion.
- [ ] Package final APK on x86 CI; initial x86 packaging and native tests passed.

### Task 3: Verification
- [x] Review against spec and fix material findings.
- [x] Document device acceptance gates and run repository checks.

User authorised implementation in this session. Execute inline on feat/reported-depth-ar.

Verification: Flutter 66 tests and analyzer pass; repository policy and 207 pinned source files pass. Camera/water shaders compile and link. Independent review complete. No connected Android device: physical tracking, alignment, rotation and thermal acceptance remain open.

Account changes clear Flutter preview context and cancel both active and pending native launches. Follow-up independent review found no remaining material defect in these guards; physical-device acceptance is still required.

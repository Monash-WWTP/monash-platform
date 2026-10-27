# CitizenFlood reported-depth AR

Status: scope approved by the user on 2026-10-27; source implementation in progress.

## Purpose and boundary

Add an optional, private Android visual aid to existing numeric water-depth
reporting. Render an already entered/reported depth above a user-selected local
reference plane. This is an illustration of an observation, not a measurement,
forecast, flood simulation or reconstruction of a historical scene.

## Approaches

Use Flutter for the existing reporting workflow and a native Kotlin Activity
using Google's ARCore Android SDK, OpenGL ES and Android UI controls for the AR
session. This gives direct access to lifecycle, tracking and depth support.
A general Flutter AR plugin adds an abstraction that needs independent depth
and lifecycle qualification. An embedded Unity runtime adds an engine and build
pipeline disproportionate to this single Android feature. Native ARCore is the
recommended approach; library versions must be verified and pinned during implementation.

## Flow

Offer “Preview depth in AR” beside a valid draft water reading and “Visualise
reported depth” in the owner's report details. Require kind=water_reading,
reference_kind=depth, unit=m and a finite nonnegative value. Exclude legacy
unstructured values, elevations tied to gauge datums and qualitative flooding.
Do not reinterpret visual flood reports as numeric measurements.

Before the camera opens, explain that the preview uses the entered value and
does not measure water. Request camera access only on entry. Check ARCore
availability and installation; handle declined installation without blocking reports.

Show a short instruction to scan a visible, safe reference surface. Let the
user tap a tracked plane and confirm it matches their recorded reference.
Never instruct users to enter floodwater; if the ground is submerged or cannot
be identified safely, exit without a preview. Do not automatically equate a
detected plane with the actual ground or a historical report's reference.

Render a bounded local patch of virtual water at reference plane + entered depth.
Use restrained animation, translucent colour and a depth scale; do not imply
street-wide coverage. Keep the entered value read-only in AR. Provide Reset
reference and Close, an always visible illustration label, and report time for
saved observations. Draft previews say “Draft depth”. No cosmetic accuracy claims.
Pause/hide the water when tracking is lost and prompt to recover or reset.

Use ARCore Depth for occlusion when available; identify a simpler plane-only
preview when depth is unavailable. Unsupported AR devices retain all normal
reporting functions. Report observations remain unchanged after viewing.

## Data and privacy

Pass only the numeric depth and necessary display context through the Flutter
platform channel. Validate inputs on both sides. Do not transmit camera frames,
request location for alignment, upload rendered media, or overwrite evidence.
Manual reference placement is not geospatial positioning. A historical report
preview depicts the selected reference now, not the original flood geometry.
No backend schema changes or new measurement method in this version.

## Verification and release

Test eligibility, units, invalid values, owner-only entry, channel errors and
return-to-draft preservation. Check install/permission refusal, unsupported
hardware, no plane, tracking loss, Activity pause/resume and resource cleanup.
Verify a known reference height on physical Android hardware, alongside visual
quality, performance and device thermal behaviour. Flutter tests/builds alone
cannot establish AR quality or measurement accuracy. Run the existing mobile
checks and document actual device results before enabling a release.

Release as an optional feature on a feature branch with the public APK unchanged
until normal signing and release acceptance. Document limitations and preserve
the observation/model distinction. No quantitative accuracy promise is made.

## Approved first-version scope

User approved this first-version scope: draft and owner-report depth previews,
manual reference placement, local-only graphics, no AR-generated measurements,
recording, public report previews or flood predictions.

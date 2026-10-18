# Scenario workspace proposal — awaiting design approval

Intent: remove unsupported spectacle, make the work sequence understandable and prevent comparisons that imply unsupported scientific conclusions. Keep the approved green/charcoal/white palette, Manrope and shared operator controls. Evidence audit: `docs/science/SIMULATION_EVIDENCE_AUDIT.md`.

## Monitoring → configure → run → inspect → compare

Monitoring remains the entry point for observations and lab records. Label their source and date and keep them separate from model outputs. The station action opens a research workspace; it must not suggest a calibrated live plant twin.

The workspace has two clear destinations: Run results and Compare scenarios. Configuration groups inputs into time window, measured/assumed influent, operating assumptions and maintenance. Weather/rainfall are labelled context-only rather than offered as predictive levers. Units and default assumptions are visible beside their fields. Running shows progress and a durable completed/failed result with Retry, preserving entered values.

Results identify the immutable run, plant, model/version, simulated period and validation status before metrics. A concise methods panel distinguishes sourced accounting arithmetic from unsupported empirical effluent relationships. No legal-compliance badges, causal explanations, best-scenario ranking or operational recommendation can be derived from the current heuristic.

## Comparison

Choose 2–4 completed runs and explicitly choose a reference. Display run IDs/model versions/time windows, then changed inputs from immutable snapshots, then results with absolute differences and percentage differences where meaningful. Percentages of screening days use percentage-point differences. A zero reference gives no relative percentage; missing metrics stay missing.

Reject duplicate, failed, cross-plant, incompatible model/artifact, date-vector or unit comparisons. Surface differences in thresholds/accounting boundaries/factors; do not hide them as process improvements. Overlay dates align by actual date/run ID rather than array index. Show empty/loading/failure/retry states and explain why a run cannot be compared. Clear selections when changing plants. Historical run browsing can be a later increment; initial correctness work uses the existing run endpoints.

Use comparison to explain what changed under documented assumptions. The present fixed-factor GHG calculation cannot evaluate maintenance/aeration-induced changes in emissions, so the UI must say so. Unsupported effluent metrics remain explicitly experimental; none becomes validated by adding a paper link.

## Evidence acceptance

Before replacing the heuristic with a scientifically supported process model, agree the plant/process, intended prediction and operating regime. Build an equation/parameter/source register, benchmark the implementation, calibrate with appropriate measurements, validate independently, quantify uncertainty and obtain scientific review. The interface cannot substitute for those steps.

## Verification

Tests must cover comparison compatibility, immutable input differences, run-ID/time-series pairing, failed/missing/zero-reference cases, cross-plant selection reset and partial outages. Browser checks cover the primary task sequence, keyboard access, narrow screens, pending/failed runs and truthful evidence labels. Existing source tests and science restrictions remain active.

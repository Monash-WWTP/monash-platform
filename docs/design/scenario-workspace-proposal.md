# Monitoring-first dashboard design — approved

Approved by the user on 2026-10-18 after choosing monitoring as the primary workflow and simulations as secondary.

Intent: remove unsupported spectacle, make the work sequence understandable and prevent comparisons that imply unsupported scientific conclusions. Keep the approved green/charcoal/white palette, Manrope and shared operator controls. Evidence audit: `docs/science/SIMULATION_EVIDENCE_AUDIT.md`.

## Priority and navigation

User direction: prioritize monitoring and keep simulations secondary. The primary journey is find a plant → inspect observations → understand data coverage → decide the next task. Retain the accessible map and searchable plant list as complementary views. Do not put simulation controls or model outputs on the monitoring overview.

The overview emphasizes latest available measurements, observation dates and sources, and missing or below-detection-limit data. Show data freshness using explicit timestamps; do not invent an operational health score, real-time status or alert severity from sparse records. Keep sampling locations distinct from treatment plants and explain unavailable data. Plant and station details expose available history, units and provenance before secondary actions.

Use one shared operator header and consistent typography, spacing, controls, focus states and empty/error states across monitoring and research. Monitoring remains the primary navigation destination. A clearly labelled Research sandbox is a secondary plant-level action, with a return link preserving monitoring context. The 3D twin remains removed.

## Secondary research workspace: configure → run → inspect → compare

The research workspace must not suggest a calibrated live plant twin. Measured observations and simulated values remain clearly distinguished; opening research does not imply that current monitoring data automatically calibrates or populates a model. Any transferred input must retain its source, date and unit.

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

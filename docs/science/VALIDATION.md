# Scientific status and limits

`effluent_v1` version 1.4.0 is **illustrative_unvalidated**. `decision_use_permitted=false` is platform policy; it is not yet carried by every API metadata field or persisted run. Passing software tests establishes implementation behavior, not scientific validity. Outputs must not determine plant control, legal compliance or certified emissions inventories.

The engine is a deterministic daily heuristic with four bounded substeps, assumed influent, demand scaling, equipment availability and maintenance effects. Carbon/nitrogen surrogates are not calibrated ASM1 states or a reactor mass balance. MLD capacity is not reactor volume or hydraulic retention time. Weather/rainfall is retained as context but not applied without a site-specific hydrologic model. No quantified uncertainty or independent validation dataset is supplied.

| Data class | Interpretation |
| --- | --- |
| Public 2023–2025 final-effluent samples | Lab snapshot; retain BDL/censoring flags |
| Source `compliance` | Source-recorded status, not an independent permit assessment |
| Citizen observation | Citizen record, not a lab sample or automatic model input |
| Scenario input | Explicit assumptions needing source, units, time basis and review |
| Model output | Illustrative result, not an observed value |

CH4/N2O intensities use assumed influent BOD5/TKN, process factors and inherited AR5 100-year GWP constants (28/265). Equations and assumptions are retained in the [historical carbon note](../legacy/dashboard/CARBON_ACCOUNTING.md). Final-effluent concentrations cannot substitute for required influent loads. The helper that did so is inactive under `legacy/research/`. Fallback screening and synthetic demo limits are not site permits.

Decision use requires reviewed sampling/analytical provenance, units and censoring; factor sources and time horizons; model boundary and conservation assumptions; calibration separated from held-out validation; residuals and uncertainty; operating-regime applicability; and a versioned acceptance record. Run records then need immutable inputs, source revisions, artifact identity, validation status and failure states. These gates remain open.

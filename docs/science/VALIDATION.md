# Scientific status and limits

`effluent_v1` version 1.4.0 is **illustrative_unvalidated**. API model metadata and persisted runs carry `decision_use_permitted=false`; this is platform policy, not scientific validation. Passing software tests establishes implementation behavior, not scientific validity. Outputs must not determine plant control, legal compliance or certified emissions inventories.

The engine is a deterministic daily heuristic with four bounded substeps, assumed influent, demand scaling, equipment availability and maintenance effects. Carbon/nitrogen surrogates are not calibrated ASM1 states or a reactor mass balance. MLD capacity is not reactor volume or hydraulic retention time. Weather/rainfall is retained as context but not applied without a site-specific hydrologic model. No quantified uncertainty or independent validation dataset is supplied.

| Data class | Interpretation |
| --- | --- |
| Public 2023–2025 final-effluent samples | Lab snapshot; retain BDL/censoring flags |
| Source `compliance` | Source-recorded status, not an independent permit assessment |
| Citizen observation | Citizen record, not a lab sample or automatic model input |
| Scenario input | Explicit assumptions needing source, units, time basis and review |
| Model output | Illustrative result, not an observed value |

The CH4/N2O helper follows the arithmetic in the guideline's revised WWTP Equations 5.25 and 5.28: influent BOD5/TKN times an emission factor, less recovered gas, converted with the stated 100-year GWP values (28/265). It is not a complete carbon inventory or an implementation of every method in the guideline. Current factors are generic defaults without process, regional, or measurement provenance. The API keeps the legacy property name `bod`, but the scenario form labels this influent input BOD5 as required by Equation 5.25; it and TKN may still use defaults. Recovery terms are subtracted as written and are not clamped, so inputs must be evidenced and plausible. This still does not validate the resulting emissions. Equations and historical assumptions are retained in the [carbon accounting note](../legacy/dashboard/CARBON_ACCOUNTING.md). Final-effluent concentrations cannot substitute for required influent loads. The helper that did so is inactive under `legacy/research/`. Fallback screening and synthetic demo limits are not site permits.

Decision use requires reviewed sampling/analytical provenance, units and censoring; factor sources and time horizons; model boundary and conservation assumptions; calibration separated from held-out validation; residuals and uncertainty; operating-regime applicability; and a versioned acceptance record. Run records then need immutable inputs, source revisions, artifact identity, validation status and failure states. These gates remain open.

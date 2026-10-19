# Simulation evidence audit — 2026-10-18

**Verdict:** current effluent outputs are an illustrative heuristic, not a validated plant model. Some GHG calculations have a traceable accounting basis, but neither cited equations nor passing software tests validate scenario predictions. Do not enable operational, regulatory or causal claims.

Scope: source-code/factor/claim fact check, with independent source verification; not a systematic literature review or scientific approval. No production measurements or private plant data were queried. Primary guideline detail was checked in the supplied, unchanged PDF because the publisher endpoint returned 403.

## Verified evidence and unresolved claims

| Component | Evidence verdict | Consequence |
| --- | --- | --- |
| Generic CH₄ `.0121`, N₂O `.0093` | Match integrated general centralized-aerobic factors in guideline Tables 5.6/5.8, printed pp.52–55 | General factors are sourced; site/process applicability and uncertainty still need justification |
| SBR, AAO, AO, oxidation ditch, aerobic-tank CSV rows | Values match the two tables; CSV “AERATION TANK” maps to source “Aerobic tank” | Preserve exact process mapping and edition rather than claiming universal applicability |
| ANAMMOX CH₄ `.02`; AGS CH₄ `.0033` | Neither process appears in cited methane Table 5.6. Values duplicate their N₂O entries | Unsupported by the claimed table. Do not silently replace with zero or advertise these methane factors as verified |
| ANAMMOX N₂O `.02` | Source category is short-cut nitrification–ANAMMOX | CSV's broader label needs an applicability review; AGS N₂O `.0033` matches aerobic granular sludge |
| CH₄ recovery arithmetic | Printed Eq.5.25 places recovery before the final `10^-3`, while defining recovery as kg CH₄/m³ | Current helper subtracts after converting gross mass, a unit-consistent interpretation, not literal equation placement. Publisher/author clarification remains open |
| N₂O arithmetic | Eq.5.28 conversion `44/28`, `10^-3`, subtraction and GWP 265 match | Equation defines its nitrogen input as Kjeldahl, but appendix language refers to total N. Document this ambiguity; ammonia/effluent cannot silently substitute |
| GWP 28/265 | Match this guideline's accounting convention | Record method/version/time horizon, not “latest universal values” |
| Effluent dynamics | No equation-level source mapping/calibration supplied for the coefficients below | No evidence supporting prediction accuracy or operational benefits |

The public CSV importer keeps factor reference metadata. The explicit API seed reads Supabase factors into per-plant records; runs consume those persisted numbers. The audit did not inspect that external table or current plant records, so it does not establish whether the two unsupported methane entries are currently assigned to a deployed plant.

## Unsupported effluent mechanisms

`effluent_v1.py` uses a 6% weekly waveform, demand/concentration scaling, fixed carbon rates (`7`, `4`, `.2`), nitrification/activity/mineralization coefficients (`2.5`, `.45`, `.3`), nitrogen/carbon surrogates (`.85`, `.8`, `.4`, `.25`), settling `.95`, and algebraic phosphorus/turbidity/pH formulas. These have no supplied equation-level study provenance or independent validation dataset. They are not an ASM stoichiometric/mass-balance implementation. Citing ASM literature cannot turn these constants into validated ASM parameters.

Rainfall/weather are context only. A controlled synthetic audit with 30-day default inputs found identical effluent results after changing to wet weather and 200 mm/day. Changing aeration availability from 100% to 30% left GHG intensity at `.2294 kgCO₂-eq/m³`, consistent with the implementation: its GHG factors do not depend on aeration/maintenance. These are software-behavior checks, not measured treatment responses.

IWA's benchmark framework specifies layout, state model, influent, test procedures and evaluation criteria. It does not validate this heuristic. Full-scale N₂O studies also demonstrate process/temporal variability; a fixed factor cannot establish an aeration intervention's causal effect.

## Historical documentation contradictions

The byte-preserved legacy carbon note incorrectly describes zero clamping, weather effects and ASM default-parameter provenance. Current code does not implement those claims. The legacy source is retained unchanged for provenance; this audit and VALIDATION.md govern current interpretation.

## Comparison integrity findings at the original audit baseline

The defects below were subsequently corrected in the monitoring-first implementation: completed-run selection, explicit reference, immutable input differences, compatibility rejection and plant-state reset now exist in source. See `apps/dashboard/src/components/comparison/comparisonModel.ts`, `services/api/app/services/comparison.py` and their tests. This records the earlier findings, not current endpoint behavior. Production acceptance remains separate.

At that original baseline, the endpoint accepted duplicate, failed, cross-plant and incompatible-date/model runs. UI selection used each scenario's latest run even when failed; chart dates came from the first series. Switching plants did not clear comparison/reference selections. Tables omitted immutable input differences, factor provenance and an explicit reference. Result differences must not be described as verified improvements.

Implemented correction: completed immutable runs only; explicit reference; unique IDs; compatible plant/model/artifact/date axis and units; threshold differences surfaced before screening comparisons; changed inputs shown from run snapshots; absolute/percentage differences with missing/zero-reference handling; no automatic winner/ranking. Method/factor differences must be visible, not hidden as operational effects.

## Scientific release path

1. Keep the current tool in an explicitly unvalidated research sandbox; remove the unsupported 3D layout.
2. Assign an actual plant/process and intended scientific question. Collect influent, flow, reactor/settler geometry, operating histories and quality-controlled measurements appropriate to the chosen process model.
3. Create a versioned equation/parameter/source/units/boundary/applicability register. Resolve recovery/TN-TKN ambiguities and unsupported methane entries before claiming verified accounting.
4. Select and verify an appropriate published process model against its reference benchmark. Calibration, held-out validation, sensitivity/uncertainty analysis and operating-regime checks need explicit acceptance criteria and independent scientific review.
5. Preserve immutable run input/source/model/validation identities. Change `decision_use_permitted` only after separate scientific authorization, never merely after adding citations.

## Primary sources

- CUWA (2024), *Guidelines for Carbon Accounting and Emission Reduction in the Urban Water Sector*, DOI [10.2166/9781789064223](https://doi.org/10.2166/9781789064223), Tables 5.6/5.8, Eqs 5.25/5.28, Appendices B.6/B.7. [Supplied PDF](../../apps/dashboard/public/references/urban-water-carbon-accounting-guidelines.pdf). Publisher URL: https://iwaponline.com/ebooks/book-pdf/1367724/wio9781789064223.pdf (web access failed; local edition checked).
- [IPCC 2019, Wastewater Treatment and Discharge](https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/5_Volume5/19R_V5_6_Ch06_Wastewater.pdf), Tables 6.3/6.8a and Annex 6A.5. Its methods/defaults must not be silently mixed with the guideline's revised factors.
- [IWA MIA benchmarking framework](https://iwa-mia.org/benchmarking/): reference environments and fair comparison requirements, not evidence of this implementation's validity.
- [IWA Good Modelling Practice task group](https://iwa-mia.org/task-groups-working-groups/): model setup, calibration/validation and variability/uncertainty.
- [Full-scale N₂O monitoring study, DOI 10.2166/wst.2023.420](https://iwaponline.com/wst/article-pdf/doi/10.2166/wst.2023.420/1343218/wst2023420.pdf): full-scale process/seasonal variability; transfer to this plant remains unproven.

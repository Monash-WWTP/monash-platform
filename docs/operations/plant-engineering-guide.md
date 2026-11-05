# Plant setup and prediction-quality guide

This guide explains what to enter today, where to enter it, and what further work is needed for defensible site predictions. It describes the current source implementation, not a claim that production or scientific acceptance has been completed. Read alongside [local demo state](local-monitoring-data.md), [administration](platform-administration.md) and [scientific validation](../science/VALIDATION.md).

## 1. Current state and intended use

NXP and PETALING-MAWAR have runnable local demonstration scenarios. Their identity, coordinates and process labels come from imported records; capacity, influent, equipment and screening assumptions are synthetic. Exact values and local run identifiers are recorded in [the demo configuration table](local-monitoring-data.md#nxp-and-petaling-mawar-runnable-demo-configurations-2026-11-05). NXP has no effluent samples in the current snapshot; PTG248 has 154. Sample count alone does not establish representative coverage or a calibration dataset.

`effluent_v1` 1.4.1 is an illustrative, deterministic daily heuristic. It is not a calibrated activated-sludge model, plant mass balance or weather forecast. Its default weekly flow oscillation is imposed, not learned from the plant. Process labels such as IETS or SBR do not select a site-specific treatment model. More precise inputs may improve the relevance of scenarios but cannot by themselves establish prediction accuracy. Model development, calibration and independent validation are separate work.

The dashboard provides monitoring, engineering configuration and the shared simulation lab. CitizenFlood provides community observations, own reports and imported monitoring-station markers with historical laboratory sample details. Its Plants list follows the shared monitoring station dataset; synthetic-only simulation plants and engineering administration remain in the dashboard. Citizen observations do not automatically become model inputs.

## 2. Where to enter information

1. Sign in. Administration requires administrator permission plus current MFA; any verified signed-in account can use the shared simulation lab.
2. Open **Administration → Stations → Configure engineering inputs** beside the station. This opens or creates its linked plant configuration. Keep the imported station code so monitoring and simulation remain linked.
3. Complete the plant fields below and save with a specific change reason. Do not use this editor to change historical laboratory values.
4. Select **Open Simulation lab**, choose the plant and review **Demo assumptions baseline**. Create a separately named scenario when preserving a baseline for comparison.
5. Enter influent, demand and equipment/maintenance assumptions; save, choose the start date and run.
6. Inspect the saved inputs and results. Compare scenarios with the same start date and horizon. A successful run is a software check, not a validation certificate.

On this demo host: [Administration](https://asus-dev.tail66f665.ts.net:10575/dashboard/admin), [Simulation lab](https://asus-dev.tail66f665.ts.net:10575/dashboard/simulation). These addresses require authorized Tailscale access and running local services; they are not public production addresses.

## 3. Plant configuration: field-by-field

| Field | What to provide | Evidence / important distinction |
| --- | --- | --- |
| Code and name | Stable facility identifier and official name | Confirm monitoring station represents the same facility; do not create duplicate codes |
| Latitude / longitude | Decimal-degree facility coordinates | Record coordinate source; verify the map position |
| Process label | Actual treatment train, e.g. SBR, with a short description | IETS is a broad label; retain it until the actual process is confirmed |
| Design capacity | Design hydraulic capacity in MLD | Design report/as-built specification; distinguish average design flow from peak capacity and current flow |
| Status | Unknown, operational or maintenance | Dated operator confirmation; unknown is preferable to an invented operating state |
| Description | Process summary, source documents, effective date and unresolved assumptions | Identify every remaining demo value explicitly |
| Equipment type/name | Pumps, aeration and clarifier resources represented in the scenario | Asset register and operator review; current model aggregates by type, not a detailed parallel-train hydraulic model |
| Availability | Effective available proportion, 0–100% | Explain the basis; not removal efficiency, motor speed, oxygen transfer efficiency or confidence in a measurement |
| Screening threshold | Metric, upper-limit value and canonical unit | Actual applicable document, revision/page/table, discharge point, effective date and averaging basis |
| Threshold applicability | Which site, outlet, period and scenario the value covers | A generic category or source-recorded compliance flag does not establish an applicable permit |
| Emission factors | CH₄ in kg CH₄/kg BOD₅ and N₂O in kg N₂O-N/kg N | Equation/table/edition and documented process/boundary applicability; do not confuse N₂O mass with N₂O-N mass |
| Factor applicability | Site/process, operating regime, period and limitations | Generic reference values are not site measurements or proof of intervention effects |
| Change reason | What changed, why, who reviewed it and source/date | Saved with versioned configuration and audit history |

Screening accepts BOD, COD, TSS, ammonia, nitrate and phosphorus in mg/L and turbidity in NTU. pH is not configurable as a single upper threshold because its limits require range semantics. Threshold duration/averaging rules are not modeled by a daily concentration comparison. Where BOD/COD/TSS limits are absent, the current model retains 50/200/100 mg/L fallback screening; removal of a setting does not disable that fallback.

No equipment record is not evidence of no equipment: the simulation resolves absent unit types to 100% availability. Review saved resolved inputs. Scenario-specific availability overrides plant defaults. Multiple units of one type currently resolve to the minimum baseline availability, not a capacity-weighted asset calculation; document any mapping simplification before interpreting results.

Unknown values must remain identified as unknown in the evidence register. The current runnable plant form requires positive capacity and factor/source text; it has no incomplete-draft save. Do not fabricate source citations to satisfy validation. The currently authorized local assumptions are explicitly labelled demo data and must be replaced or excluded during production cutover.

## 4. Scenario inputs

| Input | Units and time basis | What to enter / avoid |
| --- | --- | --- |
| Start date and horizon | UTC date; one, three or six months | Match comparisons; current engine generates daily scenario values, not observed future conditions |
| Influent flow | MLD, representative incoming daily flow | Inlet meter records with period/aggregation; 1 MLD = 1,000 m³/day |
| Influent BOD₅ | mg/L | Inlet BOD₅ laboratory result with method/date; API key `bod` retains this meaning |
| Influent COD and TSS | mg/L | Inlet results; retain dissolved/total and sampling distinctions in supporting records |
| Influent ammonia | mg/L, confirm nitrogen basis in analytical record | Do not interchange NH₃ mass and ammonia-N without an explicit supported conversion |
| Influent TKN | mg N/L | Kjeldahl nitrogen result; ammonia alone or total nitrogen is not a direct substitute |
| Demand change | Percent relative to the selected baseline | Scenario assumption with justification; current heuristic scales flow and concentrations, not a learned catchment-demand relationship |
| Equipment availability | 0–100%, by supported equipment type | Explicit scenario settings can override plant baselines |
| Maintenance | Equipment type, UTC start date, duration in days, residual availability % | Planned/actual work order; no event is an assumption of no modeled outage, not proof of no maintenance |
| Weather and rainfall | Category; mm/day | Stored context only; changing these does not currently apply a site rainfall/runoff response |
| Recovered CH₄ / N₂O | kg gas/m³ treated, consistent reporting period | Enter evidenced gas recovery normalized to treated volume; zero is an assumption unless confirmed; current subtraction is not zero-clamped |

The form currently accepts representative scalar influent values, not an uploaded measured daily time series. Retain the full time series separately for analysis/model development; do not claim it has been ingested because a mean was entered. The UI may supply defaults for omitted fields; inspect saved inputs rather than treating a default as measured data.

For a reference load calculation, flow × concentration converts as:

`load (kg/day) = flow (MLD) × concentration (mg/L)`.

The cancellation follows 10⁶ L/ML and 10⁶ mg/kg. Use contemporaneous flow and concentration for load estimation; multiplying unrelated long-period averages can differ from averaging measured loads. This identity does not make the heuristic a mass-balance model.

## 5. Evidence package to request from each plant

Keep a private evidence register with value, unit, timestamp/timezone, sample point, method, source file/revision, owner, quality flag and whether it is measured, derived or assumed. Record effective dates for engineering changes. Use controlled storage for sensitive site information, not public Git attachments.

| Priority | Request | Why it matters | Supported in current forms? |
| --- | --- | --- | --- |
| First | Design report, process flow diagram, capacity and asset list | Establish facility identity and physical interpretation | Capacity, labels, equipment summary; full documents remain external |
| First | Time-aligned inlet flow and BOD₅/COD/TSS/ammonia/TKN; outlet results | Estimate loads and evaluate predicted vs observed effluent | Representative scalar inlet values only; historical outlet monitoring retained separately |
| First | Sampling timestamps, composite/grab basis, lab methods, detection limits and QA/QC | Avoid false alignment and unqualified comparisons | Preserve in supporting evidence/import provenance; not all are scenario fields |
| First | Operating/maintenance log with actual downtime and bypass/upset events | Explain changes and identify valid operating regimes | Simplified equipment availability/maintenance only |
| First | Applicable discharge limits, averaging rules and source document | Define screening/acceptance targets correctly | Upper screening values/source text; full permit logic not implemented |
| Next | Reactor volumes, train routing, recycle/return/waste sludge flows, MLSS/MLVSS, SRT/HRT, DO, temperature, pH/alkalinity | Support a process-specific dynamic model and physical constraints | Not consumed by the current heuristic |
| Next, SBR | Cycle timing, phase volumes, fill/react/settle/decant schedule and aeration control | Represent actual batch treatment | Process label only; no SBR cycle solver |
| Next, IETS | Actual industrial wastewater composition, variability, inhibition/toxicity and treatment stages | Decide whether the selected model family is applicable | Not represented by the IETS label or current generic inputs |
| If assessing emissions | Time-resolved gas measurements, recovery, treated volume, relevant process/energy/sludge boundaries and factor sources | Validate gas accounting and inventory completeness | Factors/recovery only; no complete inventory or dynamic gas model |
| If weather matters | Local rainfall and paired inlet-flow response, catchment/sewer information | Estimate and validate a site-specific rainfall effect | Rainfall context only; requires a model extension |

These are proposed collection priorities, not universal regulatory sampling requirements. Plant operators and the scientific lead should set a feasible sampling design for the target metric, response times and safety constraints. No fixed number of samples or months guarantees validity. Cover routine and relevant wet/dry, loading and maintenance regimes; do not deliberately create unsafe operating events for data collection.

Preserve below-detection-limit flags and limits; do not silently turn censored values into zero. Distinguish missing, not sampled, invalid and true zero. Review duplicates, units, instrument calibration, lab blanks/duplicates and clock alignment. Align inlet/outlet observations with a defensible travel/residence-time basis rather than assuming same-day samples always represent the same wastewater.

## 6. Path to more precise, defensible predictions

1. **Specify the task.** Choose the target (e.g. next-day outlet ammonia), forecast horizon, site/regime and intended action. Agree acceptable error and missed-event cost before model fitting. Scenario comparison and future forecasting are different tasks.
2. **Build the paired dataset.** Collect synchronized input, operating and outlet data plus QA flags. Use the current monitoring data for descriptive context; it is not a paired influent/operating dataset by itself.
3. **Audit model adequacy.** Decide whether a calibrated empirical model, a mechanistic process model or a hybrid is justified. The current heuristic needs reviewed equations/coefficient provenance and possibly replacement; do not tune arbitrary coefficients until charts merely look convincing. ASM-family models are not automatically suitable for every IETS or SBR configuration.
4. **Separate fitting and evaluation.** Define chronological training/calibration, tuning and untouched later validation periods before fitting. Keep related samples/events together and prevent information from the future entering predictors. Test transfer to another site separately before claiming cross-site performance.
5. **Compare against simple baselines.** Evaluate last-observation persistence and a training-period site/season baseline on the same eligible observations and horizon. Greater complexity is justified by held-out improvement, not appearance.
6. **Evaluate errors and failures.** Report the metrics below by site, analyte and operating regime; examine residual plots vs time, flow and operating conditions. Investigate bias and serial dependence. Do not extrapolate performance to unobserved regimes.
7. **Quantify uncertainty.** Use a method appropriate to the chosen model and temporal dependence. Evaluate prediction-interval coverage and width on held-out data, including missing-input and shift conditions. A confidence interval for a mean is not an individual future-observation prediction interval.
8. **Review and release a version.** Record dataset snapshot, exclusions, model/code version, coefficients, calibration/validation split, baseline comparisons, uncertainty and scientific/operator approvals. Define the allowed domain, invalid-input behavior, monitoring and revalidation triggers. Operational decision use stays disabled until the separate acceptance policy is satisfied.

Suggested evaluation report (a proposal, not functionality currently implemented):

| Measure | Report | Caveat |
| --- | --- | --- |
| Bias | Mean(predicted − observed), in analyte units | Positive/negative errors can cancel |
| MAE | Mean absolute error, mg/L | Interpretable typical error; include sample count and regime |
| RMSE | Root mean square error, mg/L | Highlights large errors; sensitive to extreme observations |
| Skill | Error relative to stated simple baseline on identical validation rows | State the exact definition and reference; no universal pass mark |
| Threshold events | Recall, precision, false alarms and missed events | Use the applicable threshold/averaging basis and independent event definitions |
| Prediction interval | Nominal vs empirical coverage and interval width | Wide intervals can cover well yet be operationally unhelpful |
| Residual diagnostics | Error vs time, prediction, flow and regime; serial dependence | Aggregate scores can hide systematic failure |

Do not use R² alone as evidence of accuracy. Avoid MAPE for near-zero or censored concentrations. Report handling of detection limits explicitly; uncertainty in observations also matters. Do not advertise a percentage accuracy until the target, tolerance, dataset and held-out evaluation support it.

## 7. Completion checklist

- [ ] Every plant value has a unit, date/source and measured/derived/assumed status.
- [ ] Demo capacity, equipment, influent, screening and factor assumptions replaced or explicitly retained only for demo use.
- [ ] Actual process and boundary confirmed; unsupported factors reviewed against the equation-level audit.
- [ ] Applicable limits and averaging rules reviewed; daily screening not presented as permit compliance.
- [ ] Paired inlet/outlet/operations dataset quality-reviewed and split before fitting.
- [ ] Site model calibrated and evaluated on untouched data against simple baselines.
- [ ] Bias, MAE/RMSE, event performance and uncertainty reviewed for the intended operating domain.
- [ ] Dataset/model versions, acceptance owner, limitations and revalidation triggers recorded.
- [ ] Current encrypted coordinated backup created; production excludes unreviewed demo records.

## 8. Sources and implementation trace

The setup tables are derived from `services/api/app/admin_schemas.py`, `services/api/app/schemas.py`, `services/api/app/services/simulation.py`, `apps/dashboard/src/components/admin/SettingsForms.tsx`, `apps/dashboard/src/components/scenario/ScenarioPanel.tsx` and `packages/simulation/wwtp_sim/models/effluent_v1.py`. Synthetic values originate in `services/api/app/devdata.py`. These code references establish implemented behavior, not scientific validity.

- [Scientific status and limits](../science/VALIDATION.md) and [equation/factor evidence audit](../science/SIMULATION_EVIDENCE_AUDIT.md): repository-specific scientific status and unresolved sources.
- [NIST: How can I tell if a model fits my data?](https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd44.htm): general residual-analysis guidance; does not validate this wastewater model.
- [NIST: Prediction](https://itl.nist.gov/div898/handbook/pmd/section1/pmd132.htm): distinction between prediction uncertainty and uncertainty of the estimated response.
- [US EPA: Mechanistic Modeling—Configuration & Calibration](https://www.epa.gov/n-steps-online/mechanistic-modeling-configuration-calibration): general water-quality model calibration, validation and uncertainty principles. This is surface-water guidance, not a site-specific WWTP calibration protocol.

Reviewed against current implementation on 2026-11-05. Collection priorities and the validation workflow are proposed next steps; they are not completed experiments or implemented automatic calibration features.

# Citizen observation metrics review

Reviewed 2026-10-21. Scope: citizen mobile reports, not simulation validation. This is an evidence-informed protocol recommendation; it is not evidence that the deployed app or a new instrument is scientifically validated. Read alongside [VALIDATION.md](VALIDATION.md).

## Recommendation

Change the observation protocol before treating these records as comparable measurements. More decimals or different units do not fix an undefined measurand. For untrained citizens, default to a dated, located observation of what is visible, with optional photographic evidence. Offer numeric measurement only when the user can supply its method and necessary reference. Keep measured, estimated and categorical observations distinct in storage, exports and displays. Do not infer official hazard severity, plant performance, water quality or safe passage from a citizen report.

| Current prompt | Scientific problem | Recommended replacement |
| --- | --- | --- |
| Rainfall, mm | An accumulation without its interval and collection method is ambiguous. | Default: **Rain now** — raining / not raining / unsure. Optional **Gauge rainfall**: amount in mm, accumulation start and end, gauge/site identity and method. Retain trace separately from zero and missing. |
| Water level, m | Stage, local flood depth and elevation are different quantities. | Default: **Flooding** — water visible outside its usual channel/on normally dry land / no flooding observed here / unsure. Optional registered **Gauge reading**: station and reference revision, reading and unit. A later relative-level protocol needs a fixed reference photo/site. |
| Temperature, °C | Air, surface water and wastewater temperatures cannot be pooled. | Remove generic temperature from the main citizen flow. If retained as an instrument mode, require the subject, site/sample context and thermometer/probe method. External weather-service readings are imported data, not a citizen measurement. |
| Plant Normal / Warning / Critical | No measured variable, site-specific threshold or operational authority is established. | **Visible issue**: describe observable overflow, unusual colour, foam or odour, with unsure/not observed where applicable. These are reports, not diagnoses, permit assessments or operational status. Operators retain instrument-based plant status in the dashboard. |

The proposed categorical wording is a product protocol to pilot, not a published validated scale. “No flooding observed here” applies only to the stated location/time and visible area. “Unsure” is a real answer; an unanswered field is missing, not normal or zero. Presence does not establish extent or depth. Do not convert light/heavy rain impressions to mm or generic concern to an official warning.

## Evidence and limits

USGS defines stream stage against a reference and requires maintained datum information; it is not equivalent to channel depth. A genuine stage reading can be negative relative to its datum. Consequently the current nonnegative `water_level` contract cannot simply be renamed stage: create a new, explicitly referenced metric with appropriate signed-value validation. Preserve historical records as legacy/unspecified rather than assigning a datum retrospectively. [USGS, Stage Measurement at Gaging Stations, Techniques and Methods 3-A7, 2010](https://pubs.usgs.gov/publication/tm3A7); [USGS datum explanation](https://mn.water.usgs.gov/infodata/FAQStreamgaging.htm).

CoCoRaHS provides an established citizen precipitation protocol with observation time, daily versus multi-day accumulations, gauge catch, trace and missing values. Its guidance distinguishes zero rainfall from unavailable observations. This supports collecting an interval and method, not forcing an unequipped observer to estimate a numerical total. [CoCoRaHS mobile guide](https://media.cocorahs.org/docs/CoCoRaHS_MobileApp_User_Guide.pdf); [CoCoRaHS observing guidance](https://www.cocorahs.org/welcome.aspx?state=oh).

CrowdWater research uses site-specific reference images and virtual staff gauges for relative stream-level classes. Those classes are not universal metre depths or globally transferable severity thresholds. The 2017 modelling study used hypothetical classes derived from streamflow records, so its useful-class results do not validate arbitrary citizen classifications or CitizenFlood. [Strobl et al., 2019, Virtual Staff Gauges for Crowd-Based Stream Level Observations](https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2019.00070/full); [van Meerveld et al., 2017](https://hess.copernicus.org/articles/21/4895/2017/hess-21-4895-2017.html); [University of Zurich reference-placement protocol](https://crowdwater.ch/wp-content/uploads/2020/08/staff_gauge_placement_new_EN.pdf).

GLOBE water-temperature protocols identify the water sample, thermometer/probe and calibration procedures. A bare temperature value lacks that context. This is a model for a separate trained measurement mode, not a reason to ask ordinary flood reporters to sample floodwater. [GLOBE Water Temperature Protocol](https://www.globe.gov/documents/11865/0fd40183-f2ea-480f-82b6-8d62180d9291).

Only offer observations obtainable from a safe existing position. Do not ask users to enter water, approach an unsafe bank, collect wastewater or use their body as a depth gauge. Flood safety guidance explicitly advises against entering floodwater. A concise contextual instruction is justified even in a low-copy interface. [US National Weather Service flood safety](https://www.weather.gov/jan/beprepared-flooding).

EPA’s volunteer visual-assessment protocol records specific visible water conditions and locations for coordinator follow-up. It supports descriptive fields such as foam, sheen and debris rather than certifying plant performance from appearance. Its US seasonal and field-access guidance must not be copied as a Malaysian operating protocol without local adaptation. [EPA visual assessment](https://archive.epa.gov/water/archive/web/html/vms32.html).

## Minimal versioned record

Use a new immutable `protocol_id` and revision, distinct from API version. Retain original payloads and their original semantics. A new record needs:

- Observation kind; observed time (or explicit approximate time); submitted time separately.
- Observation location; whether selected or device-derived; device accuracy if available, without treating it as certainty about the observation itself.
- Method: categorical visual / instrument reading / estimate / imported. Numeric value and controlled unit only where applicable; category otherwise. Record missing/unsure/trace explicitly where relevant.
- Method-specific context: rain interval and gauge; stage station/reference revision; temperature subject/instrument/sample context. Do not require fictitious instrument accuracy; allow unknown precision/calibration status.
- Optional photo, reference/photo identity for relative measurements, and concise note. Evidence can improve review but a photograph alone does not certify accuracy.
- Independent review/QA state and provenance. Moderation approval is not measurement validation. Keep observer concern separate from an official alert or engineering threshold.

## Validation before scientific use

Define intended uses and a sampling plan before setting acceptance criteria. Pilot comprehension and repeated independent observations at representative sites. Pair quantitative observations with traceable reference readings matched in time/location, retaining instrument uncertainty. Report sample size, signed bias, MAE/RMSE and error distributions by method, range, site and conditions; do not rely on correlation alone. For categories, use an adjudicated reference where possible, confusion matrices, class-specific agreement and inter-observer agreement; disclose class imbalance and uncertain reference labels.

Keep protocol/threshold calibration data separate from validation held out by site and time, to limit leakage. Quantify missingness, reporting delays, duplicate reports and selection bias: volunteer reports are not a representative absence map. Audit uncertainty and privacy effects on spatial analyses. These evaluation choices are recommendations for a future validation study, not results. No numeric acceptance cutoff is asserted without an agreed use, reference uncertainty and study evidence. Until then, citizen observations remain contextual reports and must not automatically drive the simulation, compliance decisions or emergency routing.

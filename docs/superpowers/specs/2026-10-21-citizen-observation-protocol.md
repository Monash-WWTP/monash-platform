# Proposed scientifically explicit citizen-observation protocol

Status: proposed for review, not implemented. This replaces ambiguous new-report semantics; historical reports keep their original meaning. Scope is CitizenFlood observations, not the illustrative effluent simulation or laboratory monitoring.

## Purpose

Citizens report what they can directly observe without needing to diagnose treatment-plant performance or invent instrument readings. Quantitative observations require a defined measurand, reference, method and time basis. Source protocols inform the design; they do not validate this implementation or establish Malaysian decision thresholds. The evidence review is [Citizen observation metrics](../../science/CITIZEN_OBSERVATION_METRICS_REVIEW.md).

## Citizen flow

Map remains primary, with the compact floating report action. New-report choices become Flooding, Rain and Water appearance. Each starts with location/time and a short observable question, optional photo/note, then review. Quantitative readings live under Add measurement. No long permanent instructions. Unknown is explicit and never stored as zero, normal or absent.

- Flooding: report directly observed water covering a road/path/property/other surface, the observed feature and an optional photo. Record present, not observed at this place/time, or unknown. Do not ask users to enter water, estimate discharge or certify that a road is safe.
- Rain: occurrence at the observation place/time, with explicit unknown. This is an occurrence observation, not a rain-gauge total or rainfall intensity estimate.
- Water appearance: selected visible features such as discoloration, foam, floating debris, surface sheen or visible overflow, plus other/unknown. These are descriptive observations; no contamination diagnosis, plant-performance rating or causal attribution follows automatically. A no-selected-feature form is not implicitly Normal.

Final wording and categorical vocabulary require pilot comprehension and inter-observer checks; they are proposed product choices rather than externally validated scales.

## Optional quantitative readings

- Rainfall accumulation: mm, interval start/end with timezone, gauge method/type and station/site where available. Preserve trace/missing as separate states when supported; neither is zero. Do not assume24hours for legacy observations or convert totals to intensity without the recorded duration.
- Water: distinguish floodwater depth above a described local surface from river stage relative to a named stable datum/gauge. Method measured/estimated and reference identity are mandatory. A depth is nonnegative; genuine stage may be signed relative to its datum. No stage-to-discharge conversion without a site-specific reviewed relationship.
- Temperature: explicitly air or water, °C, measurement time, thermometer method, sampling position/depth where relevant and instrument/calibration provenance where known. Never turn subjective warmth or an unspecified number into a water-temperature measurement.
- Relative water-level classes are a later site-specific option only with a fixed reference/photo and versioned protocol; not global low/normal/high thresholds.

## Data contract and compatibility

Add a versioned observation contract rather than repurposing existing category/value/condition fields. Proposed envelope: protocol_version, observation_type, observed_at, location with source/accuracy, observation_method, categorical response or numeric measurement, measurement_context, optional private note/media. Required context is validated per observation type. Numerical ranges are instrument/physical validity checks, not invented environmental alert thresholds.

Existing v1 routes and stored payloads remain readable. Historical Normal/Warning/Critical stays legacy subjective condition; it is never migrated into a measured hazard class or the new appearance indicators. Historical rainfall intervals, temperature subject and water reference remain unknown when absent. New clients submit the new contract only after API deployment/capability acceptance. Mixed-version map/history views identify the observation kind and retain its units/context.

Owner data, media and precise locations remain private. The public allowlist exposes only approved observation fields and rounded location; no observer identity/private note/media path or precise reference location leaks. Moderation is publication review, not scientific validation. Citizen reports do not become laboratory data or automatic scenario inputs.

## Validation and acceptance

Software acceptance covers category-specific required context, missing/unknown/zero distinction, finite numeric validation, timestamp/interval ordering, public privacy, v1 compatibility, idempotency and mixed-version rendering. Regenerate OpenAPI and update app/dashboard/manual together for the new contract.

Field acceptance uses a written sampling plan, paired reference measurements and independent observers. Separate training/calibration from held-out sites/times/events. Assess quantitative bias/errors and uncertainty against suitable reference instruments, category confusion/inter-observer agreement, missingness, duplicate reports and spatial/temporal selection bias. Predefine intended-use acceptance criteria with domain reviewers; no arbitrary accuracy cutoff is claimed here. Pilot with Malaysian users and relevant local institutions before research/compliance or operational decision use.

Implementation plan follows written design approval. Production provisioning and public APK release remain separate gates.

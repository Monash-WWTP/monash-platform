# Practical observation context and follow-ups

Status: approved and implemented in source/local staging21October2026. Samsung revision2 workflow acceptance and field validation remain pending.

## Purpose and constraints

Improve research context using information ordinary citizens can directly obtain. Preserve the compact green map-first flow, optional evidence, explicit unsure states, immutable review and legacy reports. No assumed instrument readings, diagnoses, automatic model inputs or validated accuracy claims.

## Recommended approach

Extend the existing versioned observation protocol and reporting flow, rather than creating a separate questionnaire or inferring conditions from photos. Retain revision1 reads/submissions. Introduce revision2 for the additional semantics, advertised through capability discovery; new clients activate it only when supported. No historical backfill of absent context.

A minimal optional-fields-only change would be smaller, but would leave follow-up relationships unvalidated. A separate research survey would duplicate location/time and increase burden. The integrated protocol extension is recommended.

## Existing metadata

Continue automatic submission time, observation time defaulting to Now with an editable Earlier choice, selected/GPS location source and GPS accuracy when available. An observed time is user-reported, not certified capture time. Do not attach stale GPS accuracy after selecting another point. No additional location permission beyond the existing explicit current-location action.

## Conditions citizens can observe

Flooding retains affected surfaces and adds an optional movement question: Still / Flowing / Unsure. Only show it when flooding is observed. Omission remains missing, distinct from Unsure. Rain remains occurrence, without subjective intensity converted to rainfall totals. Water appearance retains visible feature selections; do not infer contamination or treatment performance.

Existing visual questions refer to the place/time the person is observing. Numeric modes retain instrument/estimate distinctions. Do not add an indirect-report choice without a distinct future protocol: hearsay must not silently become a direct observation.

## Photo provenance

Record camera versus gallery selection alongside the private media reference. Display this on review and owner detail. Camera selection means acquired through the app camera flow; it does not certify authenticity, subject location or observation time. Do not derive observation location/time from EXIF, expose EXIF publicly or request photo-library-wide access. Replacing/removing a photo clears its provenance. Existing media authorization and retry reuse remain mandatory.

## Linked follow-up

From an owned flooding report, offer Report an update. Start a new immutable report at the prior selected point, with a fresh editable observation time and explicit response. Optional comparison: Higher / Same / Lower / Unsure, with the prior report identified on review. This is a subjective change relative to that record, not measured depth or universal severity.

Server checks that the referenced record belongs to the caller, is a flooding observation and predates the update; reject self-links, foreign records and incompatible comparisons. Each update links to one earlier record; do not edit the original or copy its answers/photo into the new report. Explicitly identify the location as reused/selected, without inheriting old GPS accuracy. If the location changes, clear the comparison/link or require returning to the referenced point. Unknown/absence may be reported without a directional comparison.

## Privacy and compatibility

Owner and authorized reviewer views retain the context and relationship. Public output may include the movement category but omits the private follow-up identifier, photo provenance, instrument identities, notes, media and exact location. Preserve v1/legacy semantics and existing revision1 records. Unsupported services show a retry/service state; never silently discard new context. Dashboard review renders the revision and added context.

## External data

Weather/station joins remain deferred until provider, licensing, local coverage and temporal/spatial matching rules are selected. A later integration must retain provider/station/time/distance and source uncertainty separately from citizen observations. No provider access or secrets are required for this change.

## Verification and research boundary

API tests cover revision compatibility, conditional movement, missing versus unknown, media provenance consistency, ownership/time/location constraints and privacy. Flutter tests cover progressive disclosure, review/edit, photo replacement, follow-up lifecycle, account fencing and uncertain retries. Dashboard tests cover added context. Rebuild local API and staging debug APK and exercise a synthetic original/update pair on Samsung, leaving both unpublished.

Document actual device results and remaining acceptance gates. Pilot comprehension of Still/Flowing and Higher/Same/Lower with independent observers; do not claim accuracy from software tests. Production provisioning, public APK release and external weather ingestion are outside this scope.

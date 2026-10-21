# Citizen observation protocol operations

Protocol ID `citizen-observation`, revision1 is an evidence-informed collection protocol, not a validated hazard/plant-performance scale. See the [approved design](../superpowers/specs/2026-10-21-citizen-observation-protocol.md) and [evidence review](../science/CITIZEN_OBSERVATION_METRICS_REVIEW.md).

## Service/client order

Deploy and verify the API first. `/api/v2/observation-protocols` advertises supported revision/types. The new mobile form requires revision1 and all supported kinds; an unavailable/incompatible service shows Retry instead of falling back to ambiguous v1 submission. Existing v1 clients and records remain supported. Legacy endpoints deliberately exclude v2 categories, including v1 moderation/detail routes; `/api/v2/observation-history` pages mixed owner history with explicit legacy provenance. Browser sessions now use cookie path `/api` for v1/v2 and retain CSRF/origin/MFA checks. Existing browser users should sign in again to replace the old cookie path.

The main citizen choices are Flooding, Rain and Water appearance. Responses distinguish observed/not observed/unsure; appearance identifies visible features without diagnosing pollution or plant health. Add measurement offers gauge rainfall, water readings and temperature. Numeric context is required and reviewed before submission. Trace/missing rainfall has no numeric value. Historical records are never assigned missing context retrospectively.

## Registered stage references

Gauge stage is available only for an approved server-managed station reference. The station JSON payload may include `stage_reference` with `approved:true`, positive integer `revision`, `unit:"m"` and a human-facing `label`. Provision only after the datum, instrument/site, reference history and intended use have been reviewed. The revision identifies that reviewed reference; it does not certify a citizen reading. This metadata is excluded from the public station projection. Authenticated citizens can list eligible references from `/api/v2/observation-references`; the form provides sign-in/refresh access. If none exists, stage selection cannot be submitted; a described local depth remains a separate metric. No stage references were provisioned by this implementation.

Keep previous reference revisions and associated source records in controlled custody when updating a reference. Do not rewrite historical observations to a new datum. API submission validates the currently approved revision; existing observation JSON retains the revision submitted. Signed stage readings are allowed, while depth is nonnegative. Free-text reference/instrument identities stay private.

## Publication, privacy and scientific use

New reviewer queue and moderation endpoints are under `/api/v2`. Publication still requires the existing reviewer permission and MFA. A record can be reviewed only while pending. Approval publishes a structured allowlist with rounded coordinates; note, photo path, owner, exact location and private reference/instrument identities are not public. Moderation is publication review, not scientific validation. Authenticated owner history retains measurement context; public summaries are not sufficient for datum-sensitive quantitative analysis.

Before research/decision use, conduct the planned local field pilot and independent reference validation, retain sampling/instrument provenance and uncertainty, assess bias/errors/category agreement and reporting-selection bias, and record reviewed acceptance criteria. Software tests and a successful device submission cannot replace those steps. Citizen reports are not laboratory samples or automatic scenario inputs.

## Revision2: obtainable context and flooding updates

The API retains revision1 discovery keys and adds `supported_revisions:[1,2]`. Ordinary collection uses revision2 when advertised and retains revision1 collection on older services. Updates require revision2; clients never silently discard the linkage or added context. Revision1 records and retry hashes retain their original shape. Public responses report the stored protocol revision.

When flooding is observed, More context offers optional Still/Flowing/Unsure movement. Missing means unprovided, distinct from Unsure. Owned flooding detail offers Report an update from both map/list and My reports. Each update is a new immutable report at the prior selected point, with a fresh editable time, no copied evidence/answers and no inherited GPS accuracy. Optional Higher/Same/Lower/Unsure describes perceived change from that earlier report, not measured depth. Unknown/absent flooding clears movement/comparison. Changing the point clears the private link/comparison and creates an ordinary report instead.

The server requires a strictly later observation time and the exact same selected point, scopes lookup to the caller's own flooding records and rejects foreign references without disclosure. Existing revision1 flooding can be the original. The original record and publication status remain unchanged.

Optional private photo source records the camera/gallery picker action; replacement/removal clears stale provenance and upload state. It does not authenticate the image, certify its place/time or infer EXIF metadata. Review, owner detail and authorized moderation show the context. Public output permits movement but omits photo source, previous-report identifier and level comparison, alongside the existing private evidence exclusions.

No external weather join is configured. No operational response/inspection workflow is delivered by this revision; its separately approved design and implementation plan are under review. Do not interpret publication approval as investigation closure or scientific validation. Reference comparisons, observer agreement and representative repeated sampling remain field-study requirements.

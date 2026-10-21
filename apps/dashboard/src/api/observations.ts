const labels: Record<string,string> = {flooding:'Flooding',rain_occurrence:'Rain',water_appearance:'Water appearance',rainfall_accumulation:'Gauge rainfall',water_reading:'Water reading',temperature:'Temperature',present:'Observed',not_observed:'Not observed here',unknown:'Unknown',features_observed:'Features observed',trace:'Trace',missing:'Missing'}
export function observationSummary(o: Record<string,unknown>): string {
 const kind=String(o.kind)
 const reading=o.response ? labels[String(o.response)] : o.amount_state && o.amount_state!=='value' ? labels[String(o.amount_state)] : `${o.value} ${o.unit ?? ''}`
 const features=Array.isArray(o.features)?o.features.join(', '):''
 const surfaces=Array.isArray(o.surfaces)?o.surfaces.join(', '):''
 const context=[o.method,o.subject,o.reference_kind,features,surfaces,o.interval_start&&`${o.interval_start} to ${o.interval_end}`,o.reference_id&&`Reference ${o.reference_id}, revision ${o.reference_revision}`,o.reference_description,o.instrument,o.gauge_type,o.sample_context].filter(Boolean).join(' · ')
 return `${labels[kind] ?? 'Unsupported observation'}: ${reading ?? 'Unspecified'}${context ? ` · ${context}` : ''}`
}

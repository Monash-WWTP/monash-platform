import { useState, type ReactNode } from 'react'
import { adminApi, adminErrorText, type AdminStation, type PlantSettings } from '../../api/admin'
import { Button, Input, Select } from '../ui'

export const fieldClass = 'block space-y-2 text-sm font-medium'
const textAreaClass = 'block min-h-24 w-full rounded-md border border-input bg-background p-3 text-sm'
function Field({ title, children }: { title: string; children: ReactNode }) { return <label className={fieldClass}><span>{title}</span>{children}</label> }
export function Failure({ error }: { error: unknown }) { return error ? <p role="alert" className="break-words text-sm text-destructive">{adminErrorText(error)}</p> : null }

const metricUnits: Record<string, string> = { bod: 'mg/L', cod: 'mg/L', tss: 'mg/L', ammonia: 'mg/L', nitrate: 'mg/L', phosphorus: 'mg/L', turbidity: 'NTU' }

export function PlantForm({ initial, saved, discard }: { initial: PlantSettings; saved: () => Promise<void>; discard: () => void }) {
  const [value, setValue] = useState(() => structuredClone(initial))
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const field = (key: keyof PlantSettings, next: unknown) => setValue(v => ({ ...v, [key]: next }))
  const factors = value.configuration.emission_factors
  const factor = (key: keyof typeof factors, next: string | number) => setValue(v => ({ ...v, configuration: { ...v.configuration, emission_factors: { ...v.configuration.emission_factors, [key]: next } } }))
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError(null)
    try { await adminApi.savePlant(value, reason.trim()); await saved() } catch (e) { setError(e) } finally { setBusy(false) }
  }
  return <form onSubmit={submit} className="space-y-7 border-t border-border pt-6">
    <h2 className="text-xl font-semibold">{value.id ? `Edit ${initial.name}` : 'Create plant'}</h2>
    <p className="text-sm text-muted-foreground">Changes apply to future runs. Previous results and configuration history remain unchanged.</p>
    {initial.id && initial.revision === 0 && <p className="text-sm text-muted-foreground">No source references were recorded for this configuration. Review the existing values and supply their evidence before saving.</p>}
    <fieldset disabled={busy} className="space-y-6">
      <div className="grid gap-5 sm:grid-cols-2">
        <Field title="Plant code"><Input required maxLength={80} value={value.code ?? ''} onChange={e => field('code', e.target.value)} /></Field>
        <Field title="Plant name"><Input required maxLength={200} value={value.name} onChange={e => field('name', e.target.value)} /></Field>
        <Field title="Latitude"><Input required type="number" step="any" min={-90} max={90} value={value.latitude} onChange={e => field('latitude', e.target.valueAsNumber)} /></Field>
        <Field title="Longitude"><Input required type="number" step="any" min={-180} max={180} value={value.longitude} onChange={e => field('longitude', e.target.valueAsNumber)} /></Field>
        <Field title="Design capacity (MLD)"><Input required type="number" step="any" min={0.000001} value={value.capacity_mld} onChange={e => field('capacity_mld', e.target.valueAsNumber)} /></Field>
        <Field title="Process label"><Input value={value.stp_type} onChange={e => field('stp_type', e.target.value)} /></Field>
        <Field title="Status"><Select value={value.status} onChange={e => field('status', e.target.value)}>{['unknown', 'operational', 'maintenance'].map(status => <option key={status}>{status}</option>)}</Select></Field>
      </div>
      <Field title="Description"><textarea className={textAreaClass} value={value.description} onChange={e => field('description', e.target.value)} /></Field>
      <section className="space-y-4"><h3 className="font-semibold">Equipment</h3>
        {value.units.map((unit, i) => <div key={i} className="grid gap-3 border-t border-border pt-4 sm:grid-cols-4">
          <Field title="Unit type"><Select value={unit.unit_type} onChange={e => field('units', value.units.map((u, j) => j === i ? { ...u, unit_type: e.target.value } : u))}>{['pump', 'aeration', 'clarifier'].map(t => <option key={t}>{t}</option>)}</Select></Field>
          <Field title="Equipment name"><Input required value={unit.name} onChange={e => field('units', value.units.map((u, j) => j === i ? { ...u, name: e.target.value } : u))} /></Field>
          <Field title="Availability (%)"><Input required type="number" step="any" min={0} max={100} value={unit.baseline_availability} onChange={e => field('units', value.units.map((u, j) => j === i ? { ...u, baseline_availability: e.target.valueAsNumber } : u))} /></Field>
          <Button type="button" variant="default" onClick={() => field('units', value.units.filter((_, j) => j !== i))}>Remove equipment {i + 1}</Button>
        </div>)}
        <Button type="button" variant="default" onClick={() => field('units', [...value.units, { unit_type: 'pump', name: '', baseline_availability: 100 }])}>Add equipment</Button>
      </section>
      <section className="space-y-4"><h3 className="font-semibold">Screening thresholds</h3><p className="text-sm text-muted-foreground">Use a documented source and applicable unit. These settings do not establish legal compliance.</p>
        {value.configuration.thresholds.map((limit, i) => {
          const change = (next: Partial<typeof limit>) => setValue(v => ({ ...v, configuration: { ...v.configuration, thresholds: v.configuration.thresholds.map((l, j) => j === i ? { ...l, ...next } : l) } }))
          return <div key={i} className="space-y-4 border-t border-border pt-4"><div className="grid gap-4 sm:grid-cols-2">
            <Field title="Metric"><Select value={limit.metric} onChange={e => change({ metric: e.target.value, unit: metricUnits[e.target.value] })}>{Object.keys(metricUnits).map(m => <option key={m}>{m}</option>)}</Select></Field>
            <Field title="Unit"><Select value={limit.unit} onChange={e => change({ unit: e.target.value })}>{limit.unit !== metricUnits[limit.metric] && <option value={limit.unit} disabled>Unsupported: {limit.unit}</option>}<option value={metricUnits[limit.metric]}>{metricUnits[limit.metric]}</option></Select></Field>
            <Field title={`Threshold (${limit.unit})`}><Input required type="number" min={0.000001} step="any" value={limit.value} onChange={e => change({ value: e.target.valueAsNumber })} /></Field>
            <Field title="Source reference"><Input required minLength={3} maxLength={2000} value={limit.source} onChange={e => change({ source: e.target.value })} /></Field>
            <Field title="Applicability"><Input required minLength={3} maxLength={2000} value={limit.applicability} onChange={e => change({ applicability: e.target.value })} /></Field>
          </div><Button type="button" variant="default" onClick={() => setValue(v => ({ ...v, configuration: { ...v.configuration, thresholds: v.configuration.thresholds.filter((_, j) => j !== i) } }))}>Remove threshold {i + 1}</Button></div>
        })}
        <Button type="button" variant="default" onClick={() => setValue(v => ({ ...v, configuration: { ...v.configuration, thresholds: [...v.configuration.thresholds, { metric: 'bod', value: 50, unit: 'mg/L', source: '', applicability: '' }] } }))}>Add threshold</Button>
      </section>
      <section className="space-y-4"><h3 className="font-semibold">Emission factors</h3><p className="text-sm text-muted-foreground">References are supplied evidence, not independent validation. Model decision-use restrictions remain in force.</p><div className="grid gap-5 sm:grid-cols-2">
        <Field title={`Methane (${factors.ch4_unit})`}><Input required type="number" min={0} step="any" value={factors.ef_ch4} onChange={e => factor('ef_ch4', e.target.valueAsNumber)} /></Field>
        <Field title={`Nitrous oxide (${factors.n2o_unit})`}><Input required type="number" min={0} step="any" value={factors.ef_n2o} onChange={e => factor('ef_n2o', e.target.valueAsNumber)} /></Field>
        <Field title="Source reference"><Input required minLength={3} maxLength={2000} value={factors.source} onChange={e => factor('source', e.target.value)} /></Field>
        <Field title="Applicability"><Input required minLength={3} maxLength={2000} value={factors.applicability} onChange={e => factor('applicability', e.target.value)} /></Field>
      </div></section>
      <Field title="Change reason"><textarea required minLength={3} maxLength={1000} className={textAreaClass} value={reason} onChange={e => setReason(e.target.value)} /></Field>
      <Failure error={error} />
      <div className="flex flex-wrap gap-3"><Button type="submit" variant="primary">{busy ? 'Saving…' : 'Save plant'}</Button><Button type="button" variant="default" onClick={discard}>Discard edits and reload</Button></div>
    </fieldset>
  </form>
}

export function StationForm({ initial, creating, saved, discard }: { initial: AdminStation; creating: boolean; saved: () => Promise<void>; discard: () => void }) {
  const [station, setStation] = useState(() => structuredClone(initial))
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)
  async function submit(e: React.FormEvent) { e.preventDefault(); setBusy(true); setError(null); try { await adminApi.saveStation(station, reason.trim(), creating); await saved() } catch (e) { setError(e) } finally { setBusy(false) } }
  return <form onSubmit={submit} className="space-y-5 border-t border-border pt-6"><h2 className="text-xl font-semibold">{creating ? 'Create station' : `Edit ${initial.code}`}</h2><p className="text-sm text-muted-foreground">Metadata only. Historical sample values and import provenance are not edited here.</p>
    <fieldset disabled={busy} className="space-y-5"><div className="grid gap-5 sm:grid-cols-2">
      <Field title="Station code"><Input required disabled={!creating} value={station.code} onChange={e => setStation(v => ({ ...v, code: e.target.value }))} /></Field>
      {(['name', 'category', 'stp_type'] as const).map(key => <Field key={key} title={key === 'stp_type' ? 'Process label' : key === 'name' ? 'Station name' : 'Category'}><Input required={key === 'name'} value={station.payload[key] ?? ''} onChange={e => setStation(v => ({ ...v, payload: { ...v.payload, [key]: e.target.value } }))} /></Field>)}
      {(['latitude', 'longitude'] as const).map(key => <Field key={key} title={key === 'latitude' ? 'Latitude' : 'Longitude'}><Input required type="number" step="any" min={key === 'latitude' ? -90 : -180} max={key === 'latitude' ? 90 : 180} value={station.payload[key]} onChange={e => setStation(v => ({ ...v, payload: { ...v.payload, [key]: e.target.valueAsNumber } }))} /></Field>)}
    </div><Field title="Change reason"><textarea required minLength={3} maxLength={1000} className={textAreaClass} value={reason} onChange={e => setReason(e.target.value)} /></Field><Failure error={error} /><div className="flex flex-wrap gap-3"><Button type="submit" variant="primary">{busy ? 'Saving…' : 'Save station'}</Button><Button type="button" variant="default" onClick={discard}>Discard edits and reload</Button></div></fieldset>
  </form>
}

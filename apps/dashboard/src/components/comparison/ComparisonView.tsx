import { useState } from 'react'
import ReactECharts from '../dashboard/Chart'
import { useCompare, useRuns, useScenarios } from '../../api/hooks'
import { METRIC_LABELS, METRIC_UNITS } from '../../api/types'
import { useWorkspaceStore } from '../../stores/scenarioStore'
import { Button, Card, Select } from '../ui'
import { CHART } from '../dashboard/chartPalette'
import { changedInputs, metricDifference, pairResults } from './comparisonModel'

const PALETTE = [CHART.series, CHART.series2, CHART.series3, CHART.series4]
const METRICS = ['bod', 'cod', 'tss', 'ammonia', 'phosphorus', 'turbidity']
const KPIS = [
  ['compliance_pct', 'Days within screening thresholds', '%', true],
  ['exceedance_days', 'Screening exceedance days', 'days', false],
  ['capacity_utilization_pct', 'Capacity utilisation', '%', true],
  ['ch4_mean_kgco2e_m3', 'CH₄ estimate', 'kg CO₂-eq/m³', false],
  ['n2o_mean_kgco2e_m3', 'N₂O estimate', 'kg CO₂-eq/m³', false],
  ['ghg_mean_kgco2e_m3', 'Total GHG estimate', 'kg CO₂-eq/m³', false],
] as const
const number = (value: unknown) => typeof value === 'number' && Number.isFinite(value) ? value : null
const format = (value: number | null) => value == null ? '—' : value.toLocaleString(undefined, { maximumFractionDigits: 4 })
const inputValue = (value: unknown) => value === undefined ? 'Not recorded' : JSON.stringify(value)

export default function ComparisonView({ plantId }: { plantId: number }) {
  const scenarios = useScenarios(plantId)
  const candidates = (scenarios.data ?? []).filter(s => s.latest_run_id != null)
  const runQueries = useRuns(candidates.map(s => s.latest_run_id!))
  const { compareRunIds, baselineRunId, toggleCompareRun, setBaselineRunId } = useWorkspaceStore()
  const eligibleRuns = runQueries.flatMap(q => q.data?.status === 'completed' && q.data.plant_id === plantId ? [q.data] : [])
  const selected = eligibleRuns.filter(run => compareRunIds.includes(run.id))
  const ready = selected.length >= 2 && selected.length === compareRunIds.length && selected.some(r => r.id === baselineRunId)
  const comparison = useCompare(ready ? compareRunIds : [])
  const [metric, setMetric] = useState('ammonia')
  const pairs = comparison.data && ready ? pairResults(comparison.data) : null
  const reference = pairs?.find(p => p.run.id === baselineRunId)?.run

  return <div className="flex flex-col gap-4">
    <Card title="1. Choose completed runs">
      <p className="mb-3 text-xs text-muted-foreground">Select 2–4 runs from this plant. Only each scenario’s latest run is listed.</p>
      {scenarios.isLoading && <p role="status">Loading scenarios…</p>}
      {scenarios.isError && <div role="alert"><p>Scenarios could not be loaded.</p><Button onClick={() => void scenarios.refetch()}>Retry scenarios</Button></div>}
      {!scenarios.isLoading && !scenarios.isError && candidates.length === 0 && <p className="text-sm text-muted-foreground">No runs yet. Configure and run a scenario first.</p>}
      <div className="flex flex-col gap-2">
        {candidates.map((scenario, i) => {
          const query = runQueries[i], run = query.data
          const checked = !!run && compareRunIds.includes(run.id)
          const eligible = run?.status === 'completed' && run.plant_id === plantId
          return <div key={scenario.id} className="flex flex-wrap items-center gap-2 rounded border p-3">
            <label className="flex min-h-11 min-w-0 flex-1 items-center gap-3 text-sm">
              <input type="checkbox" checked={checked} disabled={!eligible || (!checked && compareRunIds.length >= 4)} onChange={() => toggleCompareRun(run!.id)} />
              <span className="min-w-0 [overflow-wrap:anywhere]">{scenario.name}<span className="block text-xs text-muted-foreground">Run #{scenario.latest_run_id} · {query.isPending ? 'Loading status…' : query.isError ? 'Status unavailable' : run?.status}</span></span>
            </label>
            {query.isError && <Button onClick={() => void query.refetch()}>Retry run</Button>}
          </div>
        })}
      </div>
      {compareRunIds.length > 0 && <Button className="mt-3" onClick={() => compareRunIds.forEach(toggleCompareRun)}>Clear selected runs</Button>}
      {selected.length !== compareRunIds.length && <p role="status" className="mt-2 text-xs text-muted-foreground">Some selected runs are unavailable or no longer listed as latest. Clear the selection and choose completed runs.</p>}
      {compareRunIds.length === 4 && <p role="status" className="mt-2 text-xs">Four runs selected. Remove one to choose another.</p>}
    </Card>
    <Card title="2. Choose a reference">
      <label htmlFor="comparison-reference" className="mb-2 block text-sm">Baseline for result differences</label>
      <Select id="comparison-reference" value={selected.some(r => r.id === baselineRunId) ? String(baselineRunId) : ''} onChange={e => setBaselineRunId(e.target.value ? Number(e.target.value) : null)}>
        <option value="">Choose a selected run</option>
        {selected.map(run => <option key={run.id} value={run.id}>{run.scenario_name} · #{run.id}</option>)}
      </Select>
      {!ready && <p className="mt-2 text-xs text-muted-foreground">Select at least two completed runs and an explicit reference to compare.</p>}
    </Card>
    {ready && comparison.isLoading && <p role="status">Checking compatibility and comparing…</p>}
    {ready && comparison.isError && <div role="alert" className="rounded border border-destructive p-3 text-sm"><p>{comparison.error.message}</p><p className="mt-2">Choose completed runs with the same plant, model/version/artifact and simulated dates.</p><Button className="mt-3" onClick={() => void comparison.refetch()}>Retry comparison</Button></div>}
    {comparison.data && ready && !comparison.isError && !pairs && <p role="alert">These results cannot be safely aligned by run and date. Choose compatible runs or retry.</p>}
    {pairs && reference && !comparison.isError && <>
      <p className="rounded border border-warning/40 bg-warning-soft p-3 text-xs">Research only · illustrative and unvalidated. Decision use is not permitted. Fixed-factor GHG accounting cannot quantify an aeration or maintenance intervention’s emissions benefit.</p>
      <Card title="3. Check run identity and changed inputs">
        <div className="space-y-4">
          {pairs.map(({ run, timeseries }) => <section key={run.id} className="min-w-0 border-b pb-4 last:border-0">
            <h3 className="text-sm font-semibold [overflow-wrap:anywhere]">{run.scenario_name} · Run #{run.id}{run.id === reference.id ? ' · Reference' : ''}</h3>
            <p className="mt-1 text-xs text-muted-foreground">{run.model_id} v{run.model_version} · {timeseries.dates[0]} → {timeseries.dates.at(-1)}</p>
            <p className="mt-1 break-all font-mono text-[10px]">Artifact: {run.artifact_digest || 'Not recorded'}</p>
            {run.id !== reference.id && <InputChanges reference={reference.input_snapshot ?? {}} candidate={run.input_snapshot ?? {}} />}
          </section>)}
        </div>
      </Card>
      <Card title="4. Inspect result differences">
        <p className="mb-3 text-xs text-muted-foreground">Each difference is relative to run #{reference.id}. Percentage measures use percentage points (pp); a zero reference has no relative percentage. Differences describe model outputs, not proven process effects.</p>
        <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="p-2 font-medium">Metric</th>{pairs.map(({ run }) => <th key={run.id} className="min-w-40 p-2 font-medium">{run.scenario_name} · #{run.id}</th>)}</tr></thead>
          <tbody>{KPIS.map(([key, label, unit, pp]) => <tr key={key} className="border-t"><th className="p-2 font-normal text-muted-foreground">{label}<span className="block text-xs">{unit}</span></th>{pairs.map(({ run }) => {
            const value = number(run.kpis[key]), delta = metricDifference(value, number(reference.kpis[key]), pp)
            return <td key={run.id} className="p-2 font-mono text-xs">{format(value)}<span className="mt-1 block text-muted-foreground">{run.id === reference.id ? 'Reference' : `Δ ${delta.absolute != null && delta.absolute > 0 ? '+' : ''}${format(delta.absolute)}${pp ? ' pp' : ` ${unit}`}${delta.relativePct == null ? '' : ` (${format(delta.relativePct)}%)`}`}</span></td>
          })}</tr>)}</tbody>
        </table></div>
      </Card>
      <Card title="Illustrative effluent overlay" action={<Select aria-label="Comparison metric" value={metric} onChange={e => setMetric(e.target.value)}>{METRICS.map(m => <option key={m} value={m}>{METRIC_LABELS[m]}</option>)}</Select>}>
        <p className="mb-2 text-xs text-muted-foreground">Aligned by actual date. Configured screening thresholds are shown in input differences, not as a common permit limit.</p>
        <ReactECharts notMerge style={{ height: 320 }} option={{ backgroundColor: 'transparent', tooltip: { trigger: 'axis' }, legend: { type: 'scroll', top: 0, textStyle: { color: CHART.axis, fontSize: 11 } }, grid: { left: 50, right: 15, top: 45, bottom: 28 },
          xAxis: { type: 'category', data: pairs[0].timeseries.dates, axisLabel: { color: CHART.axis, fontSize: 10 } },
          yAxis: { type: 'value', scale: true, name: METRIC_UNITS[metric], splitLine: { lineStyle: { color: CHART.grid } } },
          series: pairs.map(({ run, timeseries }, i) => ({ name: `${run.scenario_name} #${run.id}`, type: 'line', data: timeseries.series[metric] ?? [], showSymbol: false, lineStyle: { width: run.id === reference.id ? 3 : 1.5, color: PALETTE[i] }, itemStyle: { color: PALETTE[i] } })),
        }} />
      </Card>
    </>}
  </div>
}

function InputChanges({ reference, candidate }: { reference: Record<string, unknown>; candidate: Record<string, unknown> }) {
  const changes = changedInputs(reference, candidate)
  return <div className="mt-3 text-xs">
    {changes.some(c => /emission_factors|compliance_limits/.test(c.path)) && <p className="mb-2 rounded border border-warning p-2">Accounting factors or screening thresholds differ. Result changes cannot be attributed solely to process inputs.</p>}
    {changes.length ? <dl className="space-y-2">{changes.map(change => <div key={change.path} className="min-w-0 rounded bg-muted p-2 [overflow-wrap:anywhere]"><dt className="font-medium">{inputLabel(change.path)}</dt><dd className="mt-1 text-muted-foreground">{inputValue(change.reference)} → {inputValue(change.candidate)}</dd></div>)}</dl> : <p className="text-muted-foreground">No saved input differences.</p>}
  </div>
}

function inputLabel(path: string) {
  const labels: Record<string, string> = {
    'forecast.influent.flow': 'Assumed influent flow (MLD)', 'forecast.influent.bod': 'Assumed influent BOD₅ (mg/L)',
    'forecast.influent.cod': 'Assumed influent COD (mg/L)', 'forecast.influent.tss': 'Assumed influent TSS (mg/L)',
    'forecast.influent.ammonia': 'Assumed influent ammonia (mg/L)', 'forecast.influent.tkn': 'Assumed influent TKN (mg N/L)',
    'forecast.rainfall_mm_day': 'Rainfall context (mm/day; not applied)', 'forecast.weather': 'Weather context (not applied)',
    'forecast.demand_change_pct': 'Demand change (%)', 'forecast.demand_multiplier': 'Demand multiplier',
    'emission_factors.ef_ch4': 'Methane factor (kg CH₄/kg BOD₅)', 'emission_factors.ef_n2o': 'Nitrous oxide factor (kg N₂O-N/kg TKN)',
    'operating_parameters.capacity_mld': 'Assumed capacity (MLD)',
    'operating_parameters.ch4_recovered_kg_m3': 'Recovered CH₄ (kg/m³)', 'operating_parameters.n2o_recovered_kg_m3': 'Recovered N₂O (kg/m³)',
    'operating_parameters.aeration_availability': 'Aeration availability (%)', 'operating_parameters.pump_availability': 'Pump availability (%)',
    'operating_parameters.clarifier_availability': 'Clarifier availability (%)',
  }
  return labels[path] ?? path.replaceAll('.', ' / ').replaceAll('_', ' ')
}

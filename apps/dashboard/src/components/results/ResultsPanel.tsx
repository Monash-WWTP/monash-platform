import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

import { useRun, useTimeseries } from '../../api/hooks'
import type { Exceedance } from '../../api/types'
import { METRIC_LABELS } from '../../api/types'
import { useWorkspaceStore } from '../../stores/scenarioStore'
import { Button, Card } from '../ui'

export default function ResultsPanel({ plantId }: { plantId: number }) {
  const { activeRunId, setActiveRunId } = useWorkspaceStore()
  const query = useRun(activeRunId)
  const run = query.data?.plant_id === plantId ? query.data : undefined
  const { data: ts } = useTimeseries(run?.status === 'completed' ? activeRunId : null)
  const qc = useQueryClient()
  const retry = useMutation({ mutationFn: () => api.replayRun(run!.id), onSuccess: next => {
    setActiveRunId(next.id)
    void qc.invalidateQueries({ queryKey: ['scenarios', plantId] })
  } })
  if (activeRunId && query.isError) return <div role="alert" className="p-4 text-sm"><p>Run results are unavailable.</p><Button onClick={() => void query.refetch()}>Retry results</Button></div>
  if (activeRunId && query.isLoading) return <p role="status" className="p-4 text-sm">Loading saved run…</p>
  if (!run) return <p className="p-4 text-sm text-muted-foreground">Configure a scenario and run an illustrative model screen to inspect results.</p>
  if (run.status !== 'completed') return <div className="space-y-3 p-4 text-sm">
    <h2 className="font-semibold">{run.status === 'failed' ? 'Run failed' : 'Run in progress'} · #{run.id}</h2>
    <p>No completed results are available. Your scenario inputs have been kept.</p>
    {run.status === 'failed' ? <Button disabled={retry.isPending} onClick={() => retry.mutate()}>{retry.isPending ? 'Retrying…' : 'Retry saved inputs'}</Button> : <Button onClick={() => void query.refetch()}>Refresh run status</Button>}
    {retry.isError && <p role="alert">{retry.error.message}</p>}
  </div>

  const kpis = run.kpis

  return (
    <div className="flex flex-col gap-3 p-3">
      <Card title={`Saved run #${run.id} · ${run.scenario_name}`}>
        <p className="text-xs text-muted-foreground">{run.model_id} v{run.model_version} · {run.status} · {run.validation_status}</p>
        <p className="mt-2 text-xs">Simulated period: {ts?.dates[0] ?? run.input_snapshot?.start_date ?? 'Not recorded'} → {ts?.dates.at(-1) ?? 'Not recorded'}</p>
        <p className="mt-2 break-all font-mono text-[10px]">Artifact: {run.artifact_digest || 'Not recorded'}</p>
        <details className="mt-3 text-xs"><summary className="cursor-pointer font-medium">Saved run inputs</summary><pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-all rounded bg-muted p-3">{JSON.stringify(run.input_snapshot ?? {}, null, 2)}</pre></details>
      </Card>
      {!run.decision_use_permitted && (
        <p role="status" className="rounded border border-warning/40 bg-warning-soft p-2 text-xs text-foreground">
          Decision use is not permitted. This process model is illustrative and has not been
          validated against plant data; do not use these estimates for operations, regulatory
          reporting, or compliance determinations.
        </p>
      )}
      <Card title="Summary">
        <div className="grid grid-cols-2 gap-2">
          <Kpi
            label="Days within screening thresholds"
            value={`${display(kpis.compliance_pct)}%`}
            note="heuristic result; not a compliance rate"
          />
          <Kpi
            label="Exceedance days"
            value={display(kpis.exceedance_days)}
            note={`of ${ts?.dates.length ?? '—'} simulated`}
          />
          <Kpi
            label="Capacity utilisation"
            value={`${display(kpis.capacity_utilization_pct)}%`}
            note="mean flow / hydraulic capacity"
          />
          <Kpi
            label="Scenario GHG estimate"
            value={`${display(kpis.ghg_mean_kgco2e_m3, 3)}`}
            note="kg CO₂-eq/m³ (CH₄ + N₂O)"
          />
        </div>
      </Card>

      <Card title="Estimated scenario GHG intensity">
        <div className="flex flex-col gap-1 text-sm">
          <Row label="CH₄ (Eq. 5.25)" value={`${display(kpis.ch4_mean_kgco2e_m3, 4)} kg CO₂-eq/m³`} />
          <Row label="N₂O (Eq. 5.28)" value={`${display(kpis.n2o_mean_kgco2e_m3, 4)} kg CO₂-eq/m³`} />
          <Row label="Total" value={`${display(kpis.ghg_mean_kgco2e_m3, 4)} kg CO₂-eq/m³`} />
          <p className="mt-1 text-[10px] text-muted-foreground">
            Illustrative estimate from assumed influent BOD₅/TKN and emission factors; not a measured
            plant inventory. GWP CH₄ = 28, N₂O = 265 (IPCC AR5).
          </p>
        </div>
      </Card>

      <Card title="Model screen by configured parameter">
        <div className="flex flex-col gap-1">
          {Object.entries(kpis)
            .filter(([k]) => k.startsWith('compliance_') && k !== 'compliance_pct')
            .map(([k, v]) => {
              const metric = k.replace('compliance_', '')
              const pct = Number(v)
              return (
                <div key={k} className="flex items-center justify-between text-sm">
                  <span>{METRIC_LABELS[metric] ?? metric}</span>
                  <span
                    className={`font-mono text-xs ${pct < 100 ? 'text-destructive' : 'text-muted-foreground'}`}
                  >
                    {pct}%
                  </span>
                </div>
              )
            })}
        </div>
      </Card>

      <Card title={`Screening-threshold exceedances (${run.exceedances.length})`}>
        {run.exceedances.length === 0 ? (
          <p className="text-xs text-muted-foreground">
            No configured screening-threshold exceedances in this model run.
          </p>
        ) : (
          <div className="flex flex-col divide-y">
            {run.exceedances.map((ex, i) => (
              <ExceedanceRow key={i} ex={ex} dates={ts?.dates} />
            ))}
          </div>
        )}
      </Card>

      <p className="px-1 text-[10px] text-muted-foreground">
        Model: {run.model_id} v{run.model_version} · Run #{run.id} ·{' '}
        {new Date(run.created_at).toLocaleString()}
      </p>
    </div>
  )
}

function ExceedanceRow({ ex, dates }: { ex: Exceedance; dates?: string[] }) {
  const [open, setOpen] = useState(false)
  const days = ex.end_day - ex.start_day + 1
  return (
    <div className="text-xs">
      <button
        className="flex w-full items-center gap-1.5 py-1.5 text-left hover:bg-muted/50"
        onClick={() => setOpen((o) => !o)}
        title={`Day ${ex.start_day + 1}–${ex.end_day + 1}${
          ex.factors.length ? ` · ${ex.factors.join(', ')}` : ''
        }`}
      >
        {open ? (
          <ChevronDown className="size-3 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="size-3 shrink-0 text-muted-foreground" />
        )}
        <span className="w-16 font-medium">{METRIC_LABELS[ex.metric] ?? ex.metric}</span>
        <span className="text-muted-foreground">{days}d</span>
        <span className="ml-auto font-mono">{ex.peak_ratio}× screen threshold</span>
      </button>
      {open && (
        <div className="space-y-0.5 pb-2 pl-[18px] text-muted-foreground">
          <p>
            Day {ex.start_day + 1}–{ex.end_day + 1}
            {dates && ` · ${dates[ex.start_day]} → ${dates[ex.end_day]}`}
          </p>
          <p>
            Peak {ex.peak_value} vs screen threshold {ex.limit_value}
          </p>
          {ex.factors.length > 0 && <p>Scenario changes overlapping this interval (not proven causes): {ex.factors.join(' · ')}</p>}
        </div>
      )}
    </div>
  )
}

function Kpi({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="rounded-md border bg-muted/50 p-2">
      <div className="text-[10px] text-muted-foreground uppercase">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
      {note && <div className="text-[10px] text-muted-foreground">{note}</div>}
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono text-xs">{value}</span>
    </div>
  )
}


function display(value: unknown, digits = 1) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString(undefined, { maximumFractionDigits: digits }) : '—'
}

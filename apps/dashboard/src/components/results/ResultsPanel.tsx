import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

import { useRun, useTimeseries } from '../../api/hooks'
import type { Exceedance, Run } from '../../api/types'
import { METRIC_LABELS } from '../../api/types'
import { useWorkspaceStore } from '../../stores/scenarioStore'
import { Card } from '../ui'

export default function ResultsPanel() {
  const { activeRunId, baselineRunId } = useWorkspaceStore()
  const forecast = useWorkspaceStore((s) => s.draft.forecast)
  const { data: run } = useRun(activeRunId)
  const { data: baseline } = useRun(baselineRunId !== activeRunId ? baselineRunId : null)
  const { data: ts } = useTimeseries(activeRunId)

  if (!run) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-sm text-muted-foreground">
        Configure a scenario and run an illustrative model screen to see scenario estimates here.
      </div>
    )
  }

  const kpis = run.kpis

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-3">
      {!run.decision_use_permitted && (
        <p role="status" className="rounded border border-amber-500/40 bg-amber-500/5 p-2 text-xs text-foreground">
          Decision use is not permitted. This process model is illustrative and has not been
          validated against plant data; do not use these estimates for operations, regulatory
          reporting, or compliance determinations.
        </p>
      )}
      <Card title="Summary">
        <div className="grid grid-cols-2 gap-2">
          <Kpi
            label="Days within screening thresholds"
            value={`${kpis.compliance_pct}%`}
            note="heuristic result; not a compliance rate"
          />
          <Kpi
            label="Exceedance days"
            value={String(kpis.exceedance_days)}
            note={`of ${ts?.dates.length ?? '—'} simulated`}
          />
          <Kpi
            label="Capacity utilisation"
            value={`${kpis.capacity_utilization_pct}%`}
            note="mean flow / hydraulic capacity"
          />
          <Kpi
            label="Scenario GHG estimate"
            value={`${Number(kpis.ghg_mean_kgco2e_m3).toFixed(3)}`}
            note="kg CO₂-eq/m³ (CH₄ + N₂O)"
          />
        </div>
      </Card>

      <Card title="Estimated scenario GHG intensity">
        <div className="flex flex-col gap-1 text-sm">
          <Row label="CH₄ (Eq. 5.25)" value={`${Number(kpis.ch4_mean_kgco2e_m3).toFixed(4)} kg CO₂-eq/m³`} />
          <Row label="N₂O (Eq. 5.28)" value={`${Number(kpis.n2o_mean_kgco2e_m3).toFixed(4)} kg CO₂-eq/m³`} />
          <Row label="Total" value={`${Number(kpis.ghg_mean_kgco2e_m3).toFixed(4)} kg CO₂-eq/m³`} />
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

      {baseline && <BaselineDelta run={run} baseline={baseline} />}

      <WhatChanged run={run} baseline={baseline} forecast={forecast} />

      <Card title="Methodology & assumptions">
        <details className="text-xs text-muted-foreground">
          <summary className="cursor-pointer font-medium text-foreground">How to read this workspace</summary>
          <div className="mt-2 space-y-2 leading-relaxed">
            <p><strong>Scenario estimate:</strong> heuristic treatment assumptions project effluent quality over the selected horizon; this is not a calibrated ASM1 implementation. TKN is influent Kjeldahl nitrogen, not a TN substitute.</p>
            <p><strong>Guideline carbon accounting:</strong> CH₄ and N₂O intensity uses the configured influent/process factors and IPCC AR5 GWP values (28 and 265). Recovery inputs reduce net gas emissions; recovery is bounded at zero.</p>
            <p><strong>Scenario inputs:</strong> demand changes the illustrative flow and load assumptions. Weather and rainfall are stored as context only and do not change model results; applying them requires a site-specific hydrologic response model. Maintenance changes unit availability and may affect the process beyond the marked window because the model state recovers gradually.</p>
            <p>Results are scenario projections, not measured compliance or a substitute for plant instrumentation and engineering review.</p>
          </div>
        </details>
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

function WhatChanged({
  run,
  baseline,
  forecast,
}: {
  run: Run
  baseline?: Run
  forecast: ReturnType<typeof useWorkspaceStore.getState>['draft']['forecast']
}) {
  const changes: string[] = []
  if (forecast.demand_change_pct) changes.push(`${forecast.demand_change_pct > 0 ? '+' : ''}${forecast.demand_change_pct}% demand versus baseline`)
  if (forecast.rainfall_mm_day) changes.push(`${forecast.rainfall_mm_day} mm/day rainfall recorded (not applied)`)
  if (forecast.influent.tkn !== undefined) changes.push(`TKN set to ${forecast.influent.tkn} mg N/L`)
  if (baseline) {
    const complianceDelta = Number(run.kpis.compliance_pct) - Number(baseline.kpis.compliance_pct)
    const ghgDelta = Number(run.kpis.ghg_mean_kgco2e_m3) - Number(baseline.kpis.ghg_mean_kgco2e_m3)
    if (Math.abs(complianceDelta) >= 0.05) changes.push(`model screening score changed by ${Math.abs(complianceDelta).toFixed(1)} percentage points`)
    if (Math.abs(ghgDelta) >= 0.0005) changes.push(`scenario GHG estimate ${ghgDelta > 0 ? 'increased' : 'decreased'} by ${Math.abs(ghgDelta).toFixed(4)} kg CO₂-eq/m³`)
  }
  return (
    <Card title="What changed">
      <p className="text-xs text-muted-foreground">
        {changes.length ? changes.join(' · ') + '.' : `Baseline projection for ${run.horizon.replace('_', ' ')}; no quantitative adjustments detected.`}
      </p>
    </Card>
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

function BaselineDelta({ run, baseline }: { run: Run; baseline: Run }) {
  const deltas = [
    {
      label: 'Model screen',
      delta: Number(run.kpis.compliance_pct) - Number(baseline.kpis.compliance_pct),
      unit: ' pp',
    },
    {
      label: 'Exceedance days',
      delta: Number(run.kpis.exceedance_days) - Number(baseline.kpis.exceedance_days),
      unit: '',
    },
    {
      label: 'Capacity utilisation',
      delta:
        Number(run.kpis.capacity_utilization_pct) -
        Number(baseline.kpis.capacity_utilization_pct),
      unit: ' pp',
    },
    {
      label: 'Scenario GHG estimate',
      delta: Number(run.kpis.ghg_mean_kgco2e_m3) - Number(baseline.kpis.ghg_mean_kgco2e_m3),
      unit: ' kg CO₂-eq/m³',
    },
  ]

  return (
    <Card title="Difference vs Baseline">
      <div className="flex flex-col gap-1 text-sm">
        {deltas.map((d) => (
          <div key={d.label} className="flex items-center justify-between">
            <span className="text-muted-foreground">{d.label}</span>
            <span className="font-mono text-xs">
              {d.delta > 0 ? '+' : ''}
              {Math.abs(d.delta) < 0.005 ? '0' : d.delta.toFixed(d.unit.includes('kg') ? 4 : 1)}
              {d.unit}
            </span>
          </div>
        ))}
        <p className="mt-1 text-[10px] text-muted-foreground">
          vs "{baseline.scenario_name}" (run #{baseline.id})
        </p>
      </div>
    </Card>
  )
}

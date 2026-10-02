import ReactECharts from 'echarts-for-react'
import { useState } from 'react'

import { useCompare, useScenarios } from '../../api/hooks'
import { METRIC_LABELS, METRIC_UNITS } from '../../api/types'
import { useWorkspaceStore } from '../../stores/scenarioStore'
import { Card, Select } from '../ui'
import { CHART } from '../dashboard/chartPalette'

// shadcn neutral-preset chart palette
const PALETTE = ['#2a9d90', '#e76e50', '#274754', '#e8c468']
const COMPARE_METRICS = ['bod', 'cod', 'tss', 'ammonia', 'phosphorus', 'turbidity']

export default function ComparisonView({ plantId }: { plantId: number }) {
  const { data: scenarios } = useScenarios(plantId)
  const { compareRunIds, toggleCompareRun } = useWorkspaceStore()
  const { data: cmp, isLoading } = useCompare(compareRunIds)
  const [metric, setMetric] = useState('ammonia')

  const candidates = (scenarios ?? []).filter((s) => s.latest_run_id != null)

  return (
    <div className="flex flex-col gap-3">
      <Card title="Select runs to compare (2–4)">
        {candidates.length === 0 ? (
          <p className="text-xs text-muted-foreground">
            No completed runs yet. Run scenarios first — each scenario's latest run becomes
            comparable here.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {candidates.map((s) => {
              const selected = compareRunIds.includes(s.latest_run_id!)
              return (
                <button
                  key={s.id}
                  onClick={() => toggleCompareRun(s.latest_run_id!)}
                  className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
                    selected
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {s.name}
                  {s.is_baseline && ' (baseline)'}
                </button>
              )
            })}
          </div>
        )}
      </Card>

      {isLoading && <p className="text-sm text-muted-foreground">Comparing…</p>}

      {cmp && (
        <>
          <p className="rounded border border-amber-500/40 bg-amber-500/5 p-2 text-xs text-foreground">
            Decision use is not permitted. These illustrative results are not validated against plant
            data and must not be used for operations, regulatory reporting, compliance determinations,
            or causal conclusions.
          </p>
          <Card title="Comparison">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs text-muted-foreground">
                    <th className="py-1.5 pr-3 font-medium">Metric</th>
                    {cmp.runs.map((r) => (
                      <th key={r.id} className="py-1.5 pr-3 font-medium">
                        {r.scenario_name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <Row
                    label="Days within screening thresholds (%)"
                    values={cmp.runs.map((r) => `${r.kpis.compliance_pct}%`)}
                  />
                  <Row
                    label="Modelled threshold exceedance days"
                    values={cmp.runs.map((r) => String(r.kpis.exceedance_days))}
                  />
                  <Row
                    label="Capacity utilisation"
                    values={cmp.runs.map((r) => `${r.kpis.capacity_utilization_pct}%`)}
                  />
                  <Row
                    label="Scenario CH₄ estimate (kg CO₂-eq/m³)"
                    values={cmp.runs.map((r) => Number(r.kpis.ch4_mean_kgco2e_m3).toFixed(4))}
                  />
                  <Row
                    label="Scenario N₂O estimate (kg CO₂-eq/m³)"
                    values={cmp.runs.map((r) => Number(r.kpis.n2o_mean_kgco2e_m3).toFixed(4))}
                  />
                  <Row
                    label="Total scenario GHG estimate (kg CO₂-eq/m³)"
                    values={cmp.runs.map((r) => Number(r.kpis.ghg_mean_kgco2e_m3).toFixed(4))}
                  />
                </tbody>
              </table>
            </div>
          </Card>

          <Card
            title="Illustrative scenario effluent overlay"
            action={
              <div className="w-36">
                <Select value={metric} onChange={(e) => setMetric(e.target.value)}>
                  {COMPARE_METRICS.map((m) => (
                    <option key={m} value={m}>
                      {METRIC_LABELS[m]}
                    </option>
                  ))}
                </Select>
              </div>
            }
          >
            <ReactECharts
              notMerge
              style={{ height: 320 }}
              option={{
                backgroundColor: 'transparent',
                tooltip: { trigger: 'axis' },
                legend: { textStyle: { color: CHART.axis, fontSize: 11 }, top: 0 },
                grid: { left: 45, right: 15, top: 40, bottom: 24 },
                xAxis: {
                  type: 'category',
                  data: cmp.timeseries[0]?.dates ?? [],
                  axisLabel: { color: CHART.axis, fontSize: 10 },
                  axisLine: { lineStyle: { color: CHART.grid } },
                },
                yAxis: {
                  type: 'value',
                  scale: true,
                  name: METRIC_UNITS[metric],
                  axisLabel: { color: CHART.axis, fontSize: 10 },
                  splitLine: { lineStyle: { color: CHART.grid } },
                },
                series: [
                  ...cmp.timeseries.map((ts, i) => ({
                    name: cmp.runs[i].scenario_name,
                    type: 'line',
                    data: ts.series[metric] ?? [],
                    showSymbol: false,
                    smooth: 0.2,
                    lineStyle: { width: 1.5, color: PALETTE[i] },
                    itemStyle: { color: PALETTE[i] },
                  })),
                  ...(cmp.timeseries[0]?.compliance_limits[metric]
                    ? [
                        {
                          name: 'Limit',
                          type: 'line',
                          data: [],
                          markLine: {
                            silent: true,
                            symbol: 'none',
                            data: [{ yAxis: cmp.timeseries[0].compliance_limits[metric] }],
                            lineStyle: { color: CHART.limit, type: 'dashed', width: 1 },
                            label: { color: CHART.limit, fontSize: 10 },
                          },
                        },
                      ]
                    : []),
                ],
              }}
            />
          </Card>
        </>
      )}
    </div>
  )
}

function Row({ label, values }: { label: string; values: string[] }) {
  return (
    <tr>
      <td className="py-1.5 pr-3 text-muted-foreground">{label}</td>
      {values.map((v, i) => (
        <td key={i} className="py-1.5 pr-3 font-mono text-xs">
          {v}
        </td>
      ))}
    </tr>
  )
}

import ReactECharts from 'echarts-for-react'

import type { ScenarioInput, Timeseries } from '../../api/types'
import { METRIC_LABELS, METRIC_UNITS } from '../../api/types'
import { CHART } from './chartPalette'

const CHART_METRICS = ['bod', 'cod', 'tss', 'ammonia', 'nitrate', 'phosphorus', 'turbidity', 'ph']

function maintenanceMarkAreas(ts: Timeseries, maintenance: ScenarioInput['maintenance']) {
  const first = new Date(ts.dates[0]).getTime()
  const dayMs = 86_400_000
  return maintenance
    .map((ev) => {
      const startIdx = Math.round((new Date(ev.start_date).getTime() - first) / dayMs)
      const endIdx = startIdx + ev.duration_days
      if (endIdx < 0 || startIdx >= ts.dates.length) return null
      return [
        {
          name: `${ev.unit_type} maintenance`,
          xAxis: ts.dates[Math.max(0, startIdx)],
          itemStyle: { color: CHART.maintenance },
          label: { color: CHART.axis, fontSize: 10 },
        },
        { xAxis: ts.dates[Math.min(ts.dates.length - 1, endIdx)] },
      ]
    })
    .filter(Boolean) as object[]
}

function baseOption(ts: Timeseries, title: string) {
  return {
    backgroundColor: 'transparent',
    grid: { left: 45, right: 15, top: 32, bottom: 24 },
    title: { text: title, textStyle: { color: CHART.axis, fontSize: 12, fontWeight: 600 } },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: unknown) =>
        typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(value),
    },
    xAxis: {
      type: 'category',
      data: ts.dates,
      axisLabel: { color: CHART.axis, fontSize: 10 },
      axisLine: { lineStyle: { color: CHART.grid } },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { color: CHART.axis, fontSize: 10 },
      splitLine: { lineStyle: { color: CHART.grid } },
    },
  }
}

export default function TrendsChart({
  ts,
  maintenance,
}: {
  ts: Timeseries
  maintenance: ScenarioInput['maintenance']
}) {
  const markAreas = maintenanceMarkAreas(ts, maintenance)

  return (
    <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
      {CHART_METRICS.map((metric) => {
        const limit = ts.compliance_limits[metric]
        const values = ts.series[metric] ?? []
        const option = {
          ...baseOption(
            ts,
            `${METRIC_LABELS[metric]} ${METRIC_UNITS[metric] ? `(${METRIC_UNITS[metric]})` : ''}`,
          ),
          series: [
            {
              name: METRIC_LABELS[metric],
              type: 'line',
              data: values,
              showSymbol: false,
              smooth: 0.2,
              lineStyle: { width: 1.5, color: CHART.series },
              itemStyle: { color: CHART.series },
              markLine: limit
                ? {
                    silent: true,
                    symbol: 'none',
                    data: [{ yAxis: limit, name: 'Limit' }],
                    lineStyle: { color: CHART.limit, type: 'dashed', width: 1 },
                    label: { color: CHART.limit, formatter: 'Limit {c}', fontSize: 10 },
                  }
                : undefined,
              markArea: markAreas.length ? { data: markAreas } : undefined,
            },
          ],
        }
        return (
          <div key={metric} className="rounded-lg border bg-card p-2">
            <ReactECharts option={option} style={{ height: 200 }} notMerge />
          </div>
        )
      })}

      {ts.series.ghg_ch4 && (
        <div className="rounded-lg border bg-card p-2 xl:col-span-2">
          <ReactECharts
            notMerge
            style={{ height: 220 }}
            option={{
              ...baseOption(ts, 'GHG emission intensity (kg CO₂-eq/m³)'),
              legend: {
                textStyle: { color: CHART.axis, fontSize: 11 },
                top: 0,
                right: 0,
              },
              series: [
                {
                  name: 'CH₄ (Eq. 5.25)',
                  type: 'line',
                  data: ts.series.ghg_ch4,
                  showSymbol: false,
                  smooth: 0.2,
                  lineStyle: { width: 1.5, color: CHART.series },
                  itemStyle: { color: CHART.series },
                },
                {
                  name: 'N₂O (Eq. 5.28)',
                  type: 'line',
                  data: ts.series.ghg_n2o,
                  showSymbol: false,
                  smooth: 0.2,
                  lineStyle: { width: 1.5, color: CHART.series2 },
                  itemStyle: { color: CHART.series2 },
                  markArea: markAreas.length ? { data: markAreas } : undefined,
                },
              ],
            }}
          />
        </div>
      )}

      {ts.series.influent_flow && (
        <div className="rounded-lg border bg-card p-2 xl:col-span-2">
          <ReactECharts
            notMerge
            style={{ height: 220 }}
            option={{
              ...baseOption(ts, 'Hydraulic context'),
              legend: { textStyle: { color: CHART.axis, fontSize: 11 }, top: 0, right: 0 },
              yAxis: [
                { type: 'value', name: 'Flow (MLD)', axisLabel: { color: CHART.axis, fontSize: 10 } },
                {
                  type: 'value',
                  name: 'Capacity use (%)',
                  axisLabel: { color: CHART.axis, fontSize: 10, formatter: '{value}%' },
                },
              ],
              series: [
                {
                  name: 'Influent flow', type: 'line', yAxisIndex: 0, data: ts.series.influent_flow,
                  showSymbol: false, smooth: 0.2, lineStyle: { width: 1.5, color: CHART.series },
                  itemStyle: { color: CHART.series },
                },
                ...(ts.series.capacity_utilization
                  ? [{
                      name: 'Capacity utilisation', type: 'line', yAxisIndex: 1,
                      data: ts.series.capacity_utilization, showSymbol: false,
                      smooth: 0.2, lineStyle: { width: 1.5, color: CHART.series2 },
                      itemStyle: { color: CHART.series2 }, markArea: markAreas.length ? { data: markAreas } : undefined,
                    }]
                  : []),
              ],
            }}
          />
          <p className="px-1 text-[10px] text-muted-foreground">
            Flow is the modelled influent volume; capacity utilisation is flow divided by available hydraulic capacity.
            Shaded bands mark planned maintenance.
          </p>
        </div>
      )}
    </div>
  )
}

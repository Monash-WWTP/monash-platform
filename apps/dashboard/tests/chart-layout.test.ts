import assert from 'node:assert/strict'
import test from 'node:test'
import { echarts } from '../src/components/dashboard/chartRuntime'
import { contextChartLayout } from '../src/components/dashboard/simulationChartLayout'
import type { Timeseries } from '../src/api/types'

test('context chart title and legend occupy separate rows at narrow and desktop widths', () => {
  const ts = { run_id: 1, dates: ['2026-01-01', '2026-01-02'], series: {}, compliance_limits: {} } as Timeseries
  for (const width of [320, 900]) {
    const chart = echarts.init(null, undefined, { renderer: 'svg', ssr: true, width, height: 220 })
    try {
      chart.setOption({ ...contextChartLayout(ts, 'Hydraulic context'), animation: false,
        yAxis: [{ type: 'value' }, { type: 'value', axisLabel: { formatter: '{value}%' } }],
        series: [
          { name: 'Influent flow (MLD)', type: 'line', data: [5, 6] },
          { name: 'Capacity utilisation (%)', type: 'line', yAxisIndex: 1, data: [50, 60] },
        ] })
      const svg = chart.renderToSVGString()
      assert.match(svg, /Hydraulic context/)
      const model = chart.getModel()
      const bounds = (type: string) => {
        const view = chart.getViewOfComponentModel(model.getComponent(type))
        const box = view.group.getBoundingRect().clone()
        box.applyTransform(view.group.getComputedTransform())
        return box
      }
      const title = bounds('title'), legend = bounds('legend')
      assert.ok(legend.y >= title.y + title.height + 4, `overlap at ${width}px: ${JSON.stringify({title,legend})}`)
    } finally { chart.dispose() }
  }
})

import assert from 'node:assert/strict'
import test from 'node:test'
import { echarts } from '../src/components/dashboard/chartRuntime'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import Chart from '../src/components/dashboard/Chart'

test('the chart adapter is a renderable React component', () => {
  const html = renderToStaticMarkup(createElement(Chart, { option: {} }))
  assert.match(html, /<div/)
})

test('line charts render legends, screening thresholds and maintenance windows', () => {
  const chart = echarts.init(null, undefined, { renderer: 'svg', ssr: true, width: 600, height: 300 })
  try {
    chart.setOption({ animation: false, title: { text: 'Lab results' }, tooltip: {},
      legend: {}, grid: {}, xAxis: { type: 'category', data: ['Jan', 'Feb'] }, yAxis: {},
      series: [{ name: 'BOD', type: 'line', data: [2, 4],
        markLine: { data: [{ name: 'Screening threshold', yAxis: 3, label: { formatter: 'Screening threshold' } }] },
        markArea: { label: { show: true }, data: [[{ name: 'Maintenance', xAxis: 'Jan' }, { xAxis: 'Feb' }]] } }],
    })
    const svg = chart.renderToSVGString()
    for (const text of ['Lab results', 'BOD', 'Screening threshold', 'Maintenance']) assert.ok(svg.includes(text), text)
  } finally { chart.dispose() }
})

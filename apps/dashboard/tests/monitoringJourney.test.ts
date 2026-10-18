import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import StationDashboard from '../src/components/monitoring/StationDashboard'
import type { EffluentSample } from '../src/api/monitoring-types'

const station = { code: 'QA', name: 'Sampling location', stp_type: null, category: null, latitude: 3, longitude: 101 }
function render(matched: boolean, samples: Partial<EffluentSample>[]) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  client.setQueryData(['sample-years', 'QA'], [2025])
  client.setQueryData(['samples', 'QA', { year: 'all', compliance: 'all' }], samples)
  const html = renderToStaticMarkup(createElement(QueryClientProvider, { client },
    createElement(StationDashboard, { station, onOpenWorkspace: matched ? () => {} : undefined })))
  client.clear()
  return html
}
test('monitoring prioritizes dated observations and keeps research secondary', () => {
  const html = render(true, [
    { id: 1, sample_date: '2025-06-01', sample_point: 'Final effluent', source_year: 2025, bod: 2, bod_bdl: true },
    { id: 2, sample_date: '2025-01-01', bod: null },
  ])
  assert.match(html, /Latest available sample/)
  assert.match(html, /2025-06-01/)
  assert.match(html, /Final effluent/)
  assert.match(html, /No quantifiable readings/)
  assert.ok(html.indexOf('Recent Samples') < html.indexOf('Research sandbox'))
  assert.doesNotMatch(html, /Open Simulation Workspace/)
})
test('unmatched locations cannot open research and missing dates are explicit', () => {
  const html = render(false, [{ id: 1, sample_date: '', bod: null }])
  assert.match(html, /Observation date unavailable/)
  assert.match(html, /No linked treatment plant/)
  assert.doesNotMatch(html, /<button[^>]*>Research sandbox/)
})

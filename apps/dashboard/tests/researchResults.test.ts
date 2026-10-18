import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ResultsPanel from '../src/components/results/ResultsPanel'
import { useWorkspaceStore } from '../src/stores/scenarioStore'

function renderRun(status: string) {
  useWorkspaceStore.getState().resetWorkspace()
  useWorkspaceStore.setState({ activeRunId: 7 })
  useWorkspaceStore.getState().setInfluent({ tkn: 999 })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  client.setQueryData(['run', 7], { id: 7, plant_id: 1, status, scenario_name: 'Saved run', horizon: '1_month',
    model_id: 'effluent_v1', model_version: '1.4.0', artifact_digest: 'sha256:immutable',
    input_snapshot: { forecast: { influent: { tkn: 40 } }, maintenance: [], start_date: '2025-01-01' },
    validation_status: 'illustrative_unvalidated', decision_use_permitted: false,
    kpis: status === 'completed' ? { compliance_pct: 80, ghg_mean_kgco2e_m3: 0.2 } : {}, exceedances: [], created_at: '2025-01-01' })
  client.setQueryData(['timeseries', 7], { run_id: 7, dates: ['2025-01-01'], series: {}, compliance_limits: {} })
  // Supply the selected workspace as the SSR hydration snapshot.
  const initialState = { ...useWorkspaceStore.getInitialState() }
  Object.assign(useWorkspaceStore.getInitialState(), useWorkspaceStore.getState())
  const html = renderToStaticMarkup(createElement(QueryClientProvider, { client }, createElement(ResultsPanel, { plantId: 1 })))
  Object.assign(useWorkspaceStore.getInitialState(), initialState)
  client.clear()
  return html
}
test('failed runs expose retry without fabricated KPI cards', () => {
  const html = renderRun('failed')
  assert.match(html, /Run failed/)
  assert.match(html, /Retry saved inputs/)
  assert.doesNotMatch(html, /NaN|Capacity utilisation|Estimated scenario GHG intensity/)
})
test('completed results expose immutable run identity and inputs instead of editable draft', () => {
  const html = renderRun('completed')
  assert.match(html, /sha256:immutable/)
  assert.match(html, /2025-01-01/)
  assert.match(html, /Saved run inputs/)
  assert.doesNotMatch(html, /999|Baseline projection|Difference vs Baseline|recovery is bounded at zero|NaN/)
})

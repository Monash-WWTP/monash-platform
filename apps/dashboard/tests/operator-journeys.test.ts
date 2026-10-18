import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import WorkspacePage from '../src/pages/WorkspacePage'
import ModerationPage from '../src/pages/ModerationPage'

function render(client: QueryClient, path: string, Component: typeof WorkspacePage) {
  const routes = createElement(Routes, null,
    createElement(Route, { path: '/dashboard/plants/:plantId', element: createElement(Component) }),
    createElement(Route, { path: '/dashboard/moderation', element: createElement(Component) }))
  const router = createElement(MemoryRouter, { initialEntries: [path] }, routes)
  return renderToStaticMarkup(createElement(QueryClientProvider, { client }, router))
}

test('workspace and moderation share a recognizable route back to the platform', () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, retryOnMount: false } } })
  client.setQueryData(['plant', 1], { id: 1, code: 'QA', name: 'Review station',
    status: 'unknown', latitude: 3, longitude: 101, capacity_mld: 10,
    description: 'Synthetic fixture', units: [], compliance_limits: [] })
  client.setQueryData(['scenarios', 1], [])
  for (const [path, Component] of [['/dashboard/plants/1', WorkspacePage], ['/dashboard/moderation', ModerationPage]] as const) {
    const html = render(client, path, Component)
    assert.match(html, /href="\/"[^>]*>Monash Water/)
    assert.match(html, /href="\/dashboard"/)
  }
  assert.match(render(client, '/dashboard/plants/1', WorkspacePage), /aria-pressed="true"/)
  assert.doesNotMatch(render(client, '/dashboard/plants/1', WorkspacePage), /3D Digital Twin/)
  client.clear()
})

test('a workspace service failure offers retry rather than claiming the plant does not exist', async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, retryOnMount: false } } })
  await client.fetchQuery({ queryKey: ['plant', 1], queryFn: async () => { throw new Error('Synthetic outage') } }).catch(() => {})
  const html = render(client, '/dashboard/plants/1', WorkspacePage)
  assert.match(html, /Retry plant/)
  assert.doesNotMatch(html, /Plant not found/)
  client.clear()
})

test('research is secondary and exposes methods before a run exists', () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  client.setQueryData(['plant', 1], { id: 1, name: 'Research plant', units: [], compliance_limits: [] })
  client.setQueryData(['scenarios', 1], [])
  const html = render(client, '/dashboard/plants/1', WorkspacePage)
  for (const label of ['Research sandbox', 'Configure', 'Run results', 'Compare scenarios', 'Methods and sources', 'Context only', 'Assumed influent']) assert.ok(html.includes(label), label)
  assert.match(html, /doi.org\/10.2166\/9781789064223/)
  assert.doesNotMatch(html, /recovery is bounded at zero/)
  client.clear()
})

test('a completed run with unavailable chart data offers retry instead of an empty-run claim', async () => {
  const { useWorkspaceStore } = await import('../src/stores/scenarioStore')
  const initial = { ...useWorkspaceStore.getInitialState() }
  useWorkspaceStore.getState().resetWorkspace()
  useWorkspaceStore.setState({ activeRunId: 7 })
  Object.assign(useWorkspaceStore.getInitialState(), useWorkspaceStore.getState())
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, retryOnMount: false } } })
  client.setQueryData(['plant', 1], { id: 1, name: 'Research plant', units: [], compliance_limits: [] })
  client.setQueryData(['scenarios', 1], [])
  client.setQueryData(['run', 7], { id: 7, plant_id: 1, status: 'completed', scenario_name: 'Saved run',
    input_snapshot: {}, kpis: {}, exceedances: [], created_at: '2025-01-01', decision_use_permitted: false })
  await client.fetchQuery({ queryKey: ['timeseries', 7], queryFn: async () => { throw new Error('Synthetic chart outage') } }).catch(() => {})
  try {
    const html = render(client, '/dashboard/plants/1', WorkspacePage)
    assert.match(html, /Retry chart data/)
    assert.match(html, /Saved results remain available/)
    assert.doesNotMatch(html, /No completed simulation to chart/)
  } finally {
    Object.assign(useWorkspaceStore.getInitialState(), initial)
    useWorkspaceStore.getState().resetWorkspace()
    client.clear()
  }
})

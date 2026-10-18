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

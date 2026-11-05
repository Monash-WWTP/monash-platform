import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import SimulationLabPage from '../src/pages/SimulationLabPage'
import { monitoringLocations } from '../src/lib/monitoringLocations'

test('lab exposes a demo without claiming imported stations have engineering inputs', () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const demo = { id: 7, code: 'DEMO001', name: 'Synthetic Demonstration Plant', status: 'unknown' as const,
    latitude: 0, longitude: 0, capacity_mld: 10, description: 'Synthetic fixture' }
  const station = { code: 'PTG248', name: 'PETALING-MAWAR', latitude: 3, longitude: 101, stp_type: 'SBR', category: 'B' }
  client.setQueryData(['plants'], [demo])
  client.setQueryData(['stations'], [station])
  const html = renderToStaticMarkup(createElement(QueryClientProvider, { client },
    createElement(MemoryRouter, null, createElement(SimulationLabPage))))
  assert.match(html, /Demo simulation/)
  assert.match(html, /href="\/dashboard\/plants\/7"/)
  assert.match(html, /Engineering inputs not configured/)
  assert.match(html, /influent flow and composition/)
  assert.deepEqual(monitoringLocations([demo], [station]), [station])
  client.clear()
})

import test from 'node:test'
import assert from 'node:assert/strict'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AdminPage from '../src/pages/AdminPage'

function render(capabilities: string[], view = 'users', verified = true) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  if (verified) client.setQueryData(['admin', 'access'], { environment: 'test', model: { id: 'effluent_v1', version: '1.4.1', validation_status: 'illustrative_unvalidated', decision_use_permitted: false }, dependencies: {}, release_acceptance: 'pending_external_acceptance' })
  client.setQueryData(['account'], { id: 'self', email: 'admin@example.test', capabilities })
  const html = renderToStaticMarkup(createElement(QueryClientProvider, { client },
    createElement(MemoryRouter, { initialEntries: [`/dashboard/admin?view=${view}`] }, createElement(AdminPage))))
  client.clear()
  return html
}

test('administration fails closed for ordinary users', () => {
  const html = render(['report:own'])
  assert.match(html, /administrator permission and MFA/)
  assert.doesNotMatch(html, /Save permissions|Create plant|Create station/)
})

test('administrator can discover bounded views and report review', () => {
  const html = render(['platform:admin'])
  for (const label of ['Users', 'Plants', 'Stations', 'History', 'Status']) assert.ok(html.includes(label), label)
  assert.match(html, /href="\/dashboard\/moderation"/)
  assert.match(html, /Search users/)
})

test('new plant form requires configuration sources and reason without validation controls', () => {
  const html = render(['platform:admin'], 'plants')
  for (const label of ['Create plant', 'Design capacity', 'Source reference', 'Applicability', 'Change reason']) assert.ok(html.includes(label), label)
  assert.doesNotMatch(html, /Mark validated|Decision use permitted|Password|Secret key/)
})

test('admin transport preserves server field diagnostics for failed saves', async () => {
  const { adminApi } = await import('../src/api/admin')
  const original = globalThis.fetch
  globalThis.fetch = async () => new Response(JSON.stringify({ error: { code: 'validation_error', message: 'Check the submitted fields', details: [{ loc: ['body', 'capacity_mld'], msg: 'Must be positive' }] } }), { status: 422 })
  try {
    await assert.rejects(adminApi.permissions({ id: 'target', email: '', capabilities: [] }, [], 'test change'), error => {
      assert.equal((error as Error & { details?: unknown[] }).details?.length, 1)
      return true
    })
  } finally { globalThis.fetch = original }
})

test('admin editors send only writable fields from server records', async () => {
  const { adminApi, newPlant } = await import('../src/api/admin')
  const original = globalThis.fetch
  const bodies: Record<string, unknown>[] = []
  globalThis.fetch = async (_url, init) => { bodies.push(JSON.parse(String(init?.body))); return new Response('{}') }
  try {
    await adminApi.savePlant({ ...newPlant(), id: 1, provenance_status: 'legacy_unknown' } as ReturnType<typeof newPlant>, 'Review configuration')
    await adminApi.saveStation({ code: 'QA', revision: 'abc', payload: { name: 'QA', latitude: 3, longitude: 101, category: 'B', stp_type: null, created_at: '2025-01-01', code: 'QA' } } as Parameters<typeof adminApi.saveStation>[0], 'Review metadata', false)
    assert.equal('provenance_status' in bodies[0], false)
    assert.equal('created_at' in bodies[1], false)
    assert.equal(bodies[1].code, 'QA')
  } finally { globalThis.fetch = original }
})

test('admin errors use the API field/message validation contract', async () => {
  const { adminErrorText } = await import('../src/api/admin')
  const { ApiRequestError } = await import('../src/api/transport')
  assert.match(adminErrorText(new ApiRequestError('Invalid input', 422, 'validation_error', [{ field: 'body.capacity_mld', message: 'Must be positive' }])), /capacity_mld: Must be positive/)
})

test('capability alone does not expose settings before protected MFA probe succeeds', () => {
  const html = render(['platform:admin'], 'plants', false)
  assert.doesNotMatch(html, /Save plant|Change reason|Create plant/)
  assert.match(html, /administrator permission and MFA/)
})

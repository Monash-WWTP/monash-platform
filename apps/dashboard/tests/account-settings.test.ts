import test from 'node:test'
import assert from 'node:assert/strict'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AccountPage from '../src/pages/public/AccountPage'
import { trustedAccountActions } from '../src/api/accounts'

test('settings reject external and unexpected paths', () => {
  assert.deepEqual(trustedAccountActions({ available: true, origin: 'https://identity.example.test', actions: { profile: 'https://evil.test/if/flow/monash-account-profile/' } }), {})
})
test('signed in account exposes concise settings and escapes display labels', () => {
  const client = new QueryClient()
  client.setQueryData(['account'], { id: 'qa', email: 'qa@example.test', display_name: '<script>QA</script>', capabilities: [] })
  client.setQueryData(['account-settings'], { available: true, origin: 'https://identity.example.test', actions: { profile: 'https://identity.example.test/if/flow/monash-account-profile/' } })
  const html = renderToStaticMarkup(createElement(QueryClientProvider, { client }, createElement(AccountPage)))
  assert.match(html, /Profile/)
  assert.match(html, /&lt;script&gt;QA&lt;\/script&gt;/)
  assert.doesNotMatch(html, /Android phone to manage/)
  client.clear()
})

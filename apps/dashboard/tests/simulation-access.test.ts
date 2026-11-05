import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import OperatorAccess from '../src/components/auth/OperatorAccess'

test('ordinary signed-in research user needs neither invitation nor MFA', () => {
  const client = new QueryClient()
  client.setQueryData(['account'], { id: 'citizen', email: 'qa@example.test', capabilities: ['report:own'] })
  const html = renderToStaticMarkup(createElement(QueryClientProvider, { client }, createElement(OperatorAccess, { simulation: true })))
  assert.match(html, /Signed in as/)
  assert.doesNotMatch(html, /invitation|Verify MFA/)
  client.clear()
})

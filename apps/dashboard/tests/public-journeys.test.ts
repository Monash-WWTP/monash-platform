import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ApiRequestError } from '../src/api/transport'
import AccountPage from '../src/pages/public/AccountPage'
import LandingPage from '../src/pages/public/LandingPage'

test('signed-out accounts offer shared sign-in and registration', () => {
  const client = new QueryClient()
  client.setQueryData(['account'], null)
  client.getQueryCache().find({queryKey: ['account']})?.setState({status: 'error', error: new ApiRequestError('Sign in', 401)})
  const html = renderToStaticMarkup(createElement(QueryClientProvider, {client}, createElement(AccountPage)))
  assert.match(html, /Your account/)
  assert.match(html, /href="\/api\/v1\/auth\/login\?account_settings=true"/)
  assert.match(html, /Create account/)
  assert.doesNotMatch(html, /Android phone to manage/)
  client.clear()
})

test('home presents the latest source preview and one download entry', () => {
  const html = renderToStaticMarkup(createElement(MemoryRouter, null, createElement(LandingPage)))
  assert.match(html, /report-screen-latest\.webp/)
  assert.doesNotMatch(html, /source preview|local staging|production deployment/)
  assert.doesNotMatch(html, /Create an account/)
  assert.equal((html.match(/href="\/download"/g) ?? []).length, 1)
})

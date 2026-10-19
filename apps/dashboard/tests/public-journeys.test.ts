import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'
import AccountPage from '../src/pages/public/AccountPage'
import LandingPage from '../src/pages/public/LandingPage'

test('unavailable accounts explain status without offering a disabled registration action', () => {
  for (const path of ['/login', '/register']) {
    const html = renderToStaticMarkup(createElement(MemoryRouter, { initialEntries: [path] }, createElement(AccountPage)))
    assert.match(html, /Account availability/)
    assert.match(html, /Account service is in local staging/)
    assert.doesNotMatch(html, /<button|Create a platform account|Log in to your platform account/)
    assert.match(html, /href="\/download"/)
  }
})

test('home presents the latest source preview and one download entry', () => {
  const html = renderToStaticMarkup(createElement(MemoryRouter, null, createElement(LandingPage)))
  assert.match(html, /report-screen-latest\.webp/)
  assert.match(html, /Account availability/)
  assert.doesNotMatch(html, /Create an account/)
  assert.equal((html.match(/href="\/download"/g) ?? []).length, 1)
})

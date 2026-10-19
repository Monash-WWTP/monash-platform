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

test('home presents an actual release preview and one download entry', () => {
  const html = renderToStaticMarkup(createElement(MemoryRouter, null, createElement(LandingPage)))
  assert.match(html, /report-screen\.png/)
  assert.match(html, /Account availability/)
  assert.doesNotMatch(html, /Create an account/)
  assert.equal((html.match(/href="\/download"/g) ?? []).length, 1)
})

test('dashboard entry exposes deployment availability before navigation', async () => {
  const { JSDOM } = await import('jsdom')
  const html = renderToStaticMarkup(createElement(MemoryRouter, null, createElement(LandingPage)))
  const document = new JSDOM(html).window.document
  const entry = document.querySelector('a[href="/dashboard"]')!
  const descriptionId = entry.getAttribute('aria-describedby')
  assert.ok(descriptionId, 'Dashboard entry must point to its availability explanation')
  assert.match(document.getElementById(descriptionId)!.textContent ?? '', /not.*deployed/i)
})

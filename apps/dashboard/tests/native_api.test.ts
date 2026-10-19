import test from 'node:test'
import assert from 'node:assert/strict'
import { fetchApi } from '../src/api/transport'

test('native transport uses versioned routes and server sessions',async()=>{
 const original=globalThis.fetch
 let seen:RequestInit|undefined
 globalThis.fetch=async(input,init)=>{assert.equal(input,'/api/v1/plants');seen=init;return new Response('[]',{status:200})}
 try {assert.deepEqual(await fetchApi('/api/v1/plants'),[]);assert.equal(seen?.credentials,'include');assert.equal(new Headers(seen?.headers).get('Authorization'),null)}
 finally {globalThis.fetch=original}
})

test('stalled API requests stop with recovery guidance', async (t) => {
 const original = globalThis.fetch
 t.mock.timers.enable({ apis: ['setTimeout'] })
 globalThis.fetch = async (_input, init) => new Promise((_resolve, reject) => {
  init?.signal?.addEventListener('abort', () => reject(init.signal?.reason), { once: true })
 })
 try {
  const pending = fetchApi('/api/v1/plants')
  const rejected = assert.rejects(pending, /timed out.*retry/i)
  t.mock.timers.tick(15000)
  await rejected
 } finally { globalThis.fetch = original; t.mock.timers.reset() }
})

test('missing versioned endpoints explain service availability', async () => {
 const original = globalThis.fetch
 globalThis.fetch = async () => new Response('{"detail":"Not Found"}', { status: 404 })
 try { await assert.rejects(fetchApi('/api/v1/plants'), /service.*unavailable/i) }
 finally { globalThis.fetch = original }
})

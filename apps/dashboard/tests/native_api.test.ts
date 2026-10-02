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

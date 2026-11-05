import assert from 'node:assert/strict'
import test from 'node:test'
import { adminApi, newPlant, plantFromStation } from '../src/api/admin'

const station = { code: 'NXP', revision: 'source-version', payload: {
  name: 'NXP station', latitude: 3.08, longitude: 101.61, category: null, stp_type: 'IETS' } }

test('engineering form preserves station metadata and requires explicit capacity', () => {
  const draft = plantFromStation(station)
  assert.equal(draft.code, 'NXP')
  assert.equal(draft.name, station.payload.name)
  assert.equal(draft.latitude, station.payload.latitude)
  assert.equal(draft.stp_type, 'IETS')
  assert.ok(Number.isNaN(draft.capacity_mld))
  assert.equal(draft.id, undefined)
})

test('engineering lookup respects admin page limits and reuses an existing linked plant', async () => {
  const original = globalThis.fetch
  const linked = { ...newPlant(), id: 7, code: 'NXP', name: 'Configured plant', revision: 2 }
  const pages: number[] = []
  globalThis.fetch = async input => {
    const url = new URL(String(input), 'http://test.local')
    assert.equal(url.searchParams.get('limit'), '100')
    const offset = Number(url.searchParams.get('offset'))
    if (url.pathname.endsWith('/stations')) {
      pages.push(offset)
      return Response.json({ total: 101, items: offset === 0
        ? Array.from({ length: 100 }, (_, n) => ({ ...station, code: `OTHER-${n}` })) : [station] })
    }
    return Response.json({ total: 1, items: [linked] })
  }
  try {
    const result = await adminApi.stationEngineering('NXP')
    assert.deepEqual(pages, [0, 100])
    assert.equal(result.station.code, 'NXP')
    assert.equal(result.plant?.id, 7)
    assert.equal(result.plant?.name, 'Configured plant')
  } finally { globalThis.fetch = original }
})

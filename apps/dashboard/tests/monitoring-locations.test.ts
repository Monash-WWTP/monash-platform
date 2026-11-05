import assert from 'node:assert/strict'
import test from 'node:test'
import { monitoringLocations } from '../src/lib/monitoringLocations'

test('monitoring data remains visible before plant configuration exists', () => {
  const station = { code: 'PTG', name: 'Monitoring station', latitude: 3, longitude: 101, stp_type: null, category: null }
  assert.deepEqual(monitoringLocations([], [station]), [station])
  const plant = { id: 1, ...station, status: 'unknown' as const, description: '', capacity_mld: 10 }
  const locations = monitoringLocations([plant], [station])
  assert.equal(locations.length, 1)
  assert.equal(locations[0].capacity_mld, 10)
})

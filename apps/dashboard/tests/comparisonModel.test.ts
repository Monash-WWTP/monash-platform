import assert from 'node:assert/strict'
import test from 'node:test'
import { changedInputs, metricDifference, pairResults } from '../src/components/comparison/comparisonModel'
import type { CompareResult } from '../src/api/types'

test('differences preserve zero, missing values and percentage point semantics', () => {
  assert.deepEqual(metricDifference(12, 10, false), { absolute: 2, relativePct: 20 })
  assert.deepEqual(metricDifference(0, 10, false), { absolute: -10, relativePct: -100 })
  assert.deepEqual(metricDifference(12, 0, false), { absolute: 12, relativePct: null })
  assert.deepEqual(metricDifference(70, 50, true), { absolute: 20, relativePct: null })
  for (const value of [null, NaN, Infinity]) {
    assert.deepEqual(metricDifference(value, 10, false), { absolute: null, relativePct: null })
  }
})
test('input differences come from immutable snapshots and include accounting assumptions', () => {
  const baseline = { forecast: { influent: { bod: 200 } }, emission_factors: { ef_ch4: 0.01 }, maintenance: [] }
  const candidate = { forecast: { influent: { bod: 250 } }, emission_factors: { ef_ch4: 0.02 }, maintenance: [] }
  assert.deepEqual(changedInputs(baseline, candidate), [
    { path: 'emission_factors.ef_ch4', reference: 0.01, candidate: 0.02 },
    { path: 'forecast.influent.bod', reference: 200, candidate: 250 },
  ])
  assert.deepEqual(changedInputs(baseline, structuredClone(baseline)), [])
  assert.deepEqual(changedInputs({ maintenance: [] }, { maintenance: [{ duration_days: 2 }] }),
    [{ path: 'maintenance', reference: [], candidate: [{ duration_days: 2 }] }])
})
test('series pair by run ID regardless of response order and malformed dates fail closed', () => {
  const result = { runs: [{ id: 1 }, { id: 2 }], timeseries: [
    { run_id: 2, dates: ['2025-01-01'], series: { bod: [20] } },
    { run_id: 1, dates: ['2025-01-01'], series: { bod: [10] } },
  ] } as CompareResult
  assert.equal(pairResults(result)?.[0].timeseries.series.bod[0], 10)
  result.timeseries[0].dates = ['2025-02-01']
  assert.equal(pairResults(result), null)
  result.timeseries[0].dates = ['2025-01-01']
  result.timeseries[0].series.bod = []
  assert.equal(pairResults(result), null)
})

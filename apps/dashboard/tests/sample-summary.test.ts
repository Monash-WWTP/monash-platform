import assert from 'node:assert/strict'
import test from 'node:test'
import type { EffluentSample } from '../src/api/monitoring-types'
import { summarizeMetric } from '../src/components/monitoring/sampleSummary'

function sample(bod: number | null, bod_bdl = false): EffluentSample {
  return { id: 1, station_code: 'QA', sample_date: '2025-01-01', sampling: 1,
    sample_point: 'Final effluent', bod, bod_bdl, cod: null, cod_bdl: false,
    nh3n: null, nh3n_bdl: false, no3n: null, no3n_bdl: false, ph: null,
    ph_bdl: false, oil_grease: null, oil_grease_bdl: false, tss: null,
    tss_bdl: false, temperature: null, compliance: '', source_year: 2025 }
}

test('missing and censored measurements do not become zero', () => {
  for (const samples of [[], [sample(null)], [sample(2, true)], [sample(null), sample(2, true)]]) {
    assert.deepEqual(summarizeMetric(samples, 'bod'), {
      totalCount: samples.length, quantifiedCount: 0, mean: null, max: null,
    })
  }
})

test('summaries use only quantified readings and preserve total count', () => {
  assert.deepEqual(summarizeMetric([sample(2), sample(4), sample(null), sample(5, true)], 'bod'), {
    totalCount: 4, quantifiedCount: 2, mean: 3, max: 4,
  })
})

test('a measured zero remains a quantified value', () => {
  assert.deepEqual(summarizeMetric([sample(0)], 'bod'), {
    totalCount: 1, quantifiedCount: 1, mean: 0, max: 0,
  })
})

test('temperature needs no censoring flag and does not reuse BOD values', () => {
  assert.deepEqual(summarizeMetric([{ ...sample(100, true), temperature: 24 }], 'temperature'), {
    totalCount: 1, quantifiedCount: 1, mean: 24, max: 24,
  })
})

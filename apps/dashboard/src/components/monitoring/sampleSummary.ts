import type { EffluentSample } from '../../api/monitoring-types'

/** Summarize quantified observations only; a detection limit is not a measurement. */
export function summarizeMetric(samples: EffluentSample[], metric: string) {
  const values = samples
    .filter(sample => !sample[`${metric}_bdl` as keyof EffluentSample])
    .map(sample => sample[metric as keyof EffluentSample])
    .filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
  return {
    totalCount: samples.length,
    quantifiedCount: values.length,
    mean: values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null,
    max: values.length ? Math.max(...values) : null,
  }
}

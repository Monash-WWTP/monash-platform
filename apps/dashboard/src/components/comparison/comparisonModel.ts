import type { CompareResult } from '../../api/types'

export function metricDifference(value: number | null, reference: number | null, percentagePoints: boolean) {
  if (value == null || reference == null || !Number.isFinite(value) || !Number.isFinite(reference)) {
    return { absolute: null, relativePct: null }
  }
  return { absolute: value - reference,
    relativePct: percentagePoints || reference === 0 ? null : (value - reference) / Math.abs(reference) * 100 }
}

export function changedInputs(reference: Record<string, unknown>, candidate: Record<string, unknown>):
  Array<{ path: string; reference: unknown; candidate: unknown }> {
  const changes: Array<{ path: string; reference: unknown; candidate: unknown }> = []
  function visit(a: unknown, b: unknown, path: string) {
    if (a && b && typeof a === 'object' && typeof b === 'object' && !Array.isArray(a) && !Array.isArray(b)) {
      const left = a as Record<string, unknown>, right = b as Record<string, unknown>
      for (const key of [...new Set([...Object.keys(left), ...Object.keys(right)])].sort()) {
        visit(left[key], right[key], path ? `${path}.${key}` : key)
      }
    } else if (JSON.stringify(a) !== JSON.stringify(b)) changes.push({ path, reference: a, candidate: b })
  }
  visit(reference, candidate, '')
  return changes
}

/** Fail closed if a response cannot be paired and overlaid without guessing. */
export function pairResults(result: CompareResult) {
  if (result.runs.length < 2 || result.runs.length !== result.timeseries.length ||
      new Set(result.runs.map(run => run.id)).size !== result.runs.length ||
      new Set(result.timeseries.map(ts => ts.run_id)).size !== result.timeseries.length) return null
  const pairs = result.runs.map(run => ({ run, timeseries: result.timeseries.find(ts => ts.run_id === run.id)! }))
  const dates = pairs[0]?.timeseries?.dates
  const metrics = Object.keys(pairs[0]?.timeseries?.series ?? {}).sort()
  if (!dates?.length || !metrics.length || new Set(dates).size !== dates.length ||
      dates.some((date, i) => !/^\d{4}-\d{2}-\d{2}$/.test(date) || (i > 0 && date <= dates[i - 1]))) return null
  if (pairs.some(({ timeseries: ts }) => !ts || JSON.stringify(ts.dates) !== JSON.stringify(dates) ||
    JSON.stringify(Object.keys(ts.series).sort()) !== JSON.stringify(metrics) ||
    Object.values(ts.series).some(values => values.length !== dates.length || values.some(v => !Number.isFinite(v))))) return null
  return pairs
}

import type { Timeseries } from '../../api/types'
import { CHART } from './chartPalette'

export function baseOption(ts: Timeseries, title: string) {
  return {
    backgroundColor: 'transparent',
    grid: { left: 45, right: 15, top: 32, bottom: 24 },
    title: { text: title, top: 0, left: 0, padding: 0, textStyle: { color: CHART.axis, fontSize: 12, fontWeight: 600 } },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: unknown) =>
        typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(value),
    },
    xAxis: {
      type: 'category',
      data: ts.dates,
      axisLabel: { color: CHART.axis, fontSize: 10 },
      axisLine: { lineStyle: { color: CHART.grid } },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { color: CHART.axis, fontSize: 10 },
      splitLine: { lineStyle: { color: CHART.grid } },
    },
  }
}

/** Reserve separate rows for title and scrollable legend on narrow charts. */
export function contextChartLayout(ts: Timeseries, title: string) {
  return {
    ...baseOption(ts, title),
    grid: { left: 48, right: 48, top: 72, bottom: 28 },
    legend: { type: 'scroll', left: 0, right: 0, top: 28,
      textStyle: { color: CHART.axis, fontSize: 11 } },
  }
}


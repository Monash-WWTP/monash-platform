import EChartsReactCore from 'echarts-for-react/esm/core'
import type { EChartsReactProps } from 'echarts-for-react/esm/types'
import { echarts } from './chartRuntime'

/** Shared line-chart runtime; avoid loading unused chart types and renderers. */
export default function Chart(props: EChartsReactProps) {
  return <EChartsReactCore {...props} echarts={echarts} opts={{ ...props.opts, renderer: 'svg' }} />
}

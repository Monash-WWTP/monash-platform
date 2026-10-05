import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { ArrowRight, FlaskConical } from 'lucide-react'

import { useSamples, useSampleYears, type SampleFilters } from '@/api/monitoring'
import { SAMPLE_METRICS, type Station } from '@/api/monitoring-types'
import { CHART } from '@/components/dashboard/chartPalette'
import {
  Card,
  SegmentGroup,
  ShadSelect,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Button,
} from '@/components/ui'

const METRIC_KEYS = Object.keys(SAMPLE_METRICS)

export default function StationDashboard({
  station,
  onOpenWorkspace,
}: {
  station: Station
  onOpenWorkspace: () => void
}) {
  const [year, setYear] = useState<SampleFilters['year']>('all')
  const [compliance, setCompliance] = useState<SampleFilters['compliance']>('all')
  const [metric, setMetric] = useState('bod')

  const { data: years } = useSampleYears(station.code)
  const { data: samples, isLoading } = useSamples(station.code, { year, compliance })

  const meta = SAMPLE_METRICS[metric]
  const stats = useMemo(() => {
    if (!samples?.length) return null
    const vals = samples
      .filter((s) => !s[`${metric}_bdl` as keyof typeof s])
      .map((s) => s[metric as keyof typeof s] as number | null)
      .filter((v): v is number => v != null)
    const reportedStatuses = samples.filter((s) => s.compliance === 'Comply' || s.compliance === 'Not Comply')
    const complyCount = reportedStatuses.filter((s) => s.compliance === 'Comply').length
    return {
      n: samples.length,
      avg: vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0,
      max: vals.length ? Math.max(...vals) : 0,
      reportedComplyPct: reportedStatuses.length ? (100 * complyCount) / reportedStatuses.length : null,
    }
  }, [samples, metric])

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-3">
      <Card title="Station">
        <div className="flex items-center gap-2">
          <FlaskConical className="size-4 text-primary" />
          <span className="text-sm font-semibold">{station.name}</span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          {station.code} · {station.stp_type ?? 'STP'} · Source category: {station.category ?? 'not recorded'}
        </p>
        <Button
          variant="primary"
          className="mt-3 flex w-full items-center justify-center gap-1.5"
          onClick={onOpenWorkspace}
        >
          Open Simulation Workspace <ArrowRight className="size-3.5" />
        </Button>
      </Card>

      <Card title="Filters">
        <div className="flex flex-col gap-3">
          <div>
            <p className="mb-1 text-xs font-medium text-muted-foreground">Year</p>
            <SegmentGroup
              options={[
                { value: 'all', label: 'All' },
                ...(years ?? []).map((y) => ({ value: String(y), label: String(y) })),
              ]}
              value={String(year)}
              onChange={(v) => setYear(v === 'all' ? 'all' : Number(v))}
            />
          </div>
          <div>
            <p className="mb-1 text-xs font-medium text-muted-foreground">Dataset-reported status</p>
            <SegmentGroup
              options={[
                { value: 'all', label: 'All' },
                { value: 'Comply', label: 'Reported comply' },
                { value: 'Not Comply', label: 'Reported not comply' },
              ]}
              value={compliance}
              onChange={(v) => setCompliance(v as SampleFilters['compliance'])}
            />
          </div>
          <div>
            <p className="mb-1 text-xs font-medium text-muted-foreground">Parameter</p>
            <ShadSelect value={metric} onValueChange={setMetric}>
              <SelectTrigger className="h-8 w-full border-border bg-muted text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {METRIC_KEYS.map((k) => (
                  <SelectItem key={k} value={k}>
                    {SAMPLE_METRICS[k].label}
                    {SAMPLE_METRICS[k].unit && ` (${SAMPLE_METRICS[k].unit})`}
                  </SelectItem>
                ))}
              </SelectContent>
            </ShadSelect>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Status is reported by the source dataset. No station-specific permit limits are
            configured, so these charts do not determine legal compliance.
          </p>
        </div>
      </Card>

      {stats && (
        <Card title={`${meta.label} Summary`}>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <Stat label="Samples" value={String(stats.n)} />
            <Stat
              label="Dataset-reported comply"
              value={stats.reportedComplyPct == null ? '—' : `${stats.reportedComplyPct.toFixed(0)}%`}
            />
            <Stat label={`Mean ${meta.label}`} value={`${stats.avg.toFixed(1)} ${meta.unit}`} />
            <Stat label={`Max ${meta.label}`} value={`${stats.max.toFixed(1)} ${meta.unit}`} />
          </div>
        </Card>
      )}

      <Card title={`${meta.label} Trend (lab results)`}>
        {isLoading ? (
          <p className="text-xs text-muted-foreground">Loading samples…</p>
        ) : !samples?.length ? (
          <p className="text-xs text-muted-foreground">No samples match the current filters.</p>
        ) : (
          <ReactECharts
            notMerge
            style={{ height: 220 }}
            option={{
              backgroundColor: 'transparent',
              grid: { left: 38, right: 12, top: 14, bottom: 22 },
              tooltip: { trigger: 'axis' },
              xAxis: {
                type: 'category',
                data: samples.map((s) => s.sample_date),
                axisLabel: { color: CHART.axis, fontSize: 9 },
                axisLine: { lineStyle: { color: CHART.grid } },
              },
              yAxis: {
                type: 'value',
                scale: true,
                axisLabel: { color: CHART.axis, fontSize: 9 },
                splitLine: { lineStyle: { color: CHART.grid } },
              },
              series: [
                {
                  type: 'line',
                  data: samples.map((s) =>
                    s[`${metric}_bdl` as keyof typeof s]
                      ? null
                      : s[metric as keyof typeof s],
                  ),
                  showSymbol: true,
                  symbolSize: 4,
                  lineStyle: { width: 1.5, color: CHART.series },
                  itemStyle: { color: CHART.series },
                },
              ],
            }}
          />
        )}
      </Card>

      <Card title="GHG emissions">
        <p className="text-xs text-muted-foreground">
          Not estimated from these lab samples. The available BOD and nitrogen values are effluent
          measurements; the cited calculation requires influent measurements and plant operating data.
        </p>
      </Card>

      {!!samples?.length && (
        <Card title="Recent Samples">
          <div className="max-h-64 overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-border">
                  <TableHead className="h-7 text-[10px]">Date</TableHead>
                  <TableHead className="h-7 text-[10px]">BOD</TableHead>
                  <TableHead className="h-7 text-[10px]">COD</TableHead>
                  <TableHead className="h-7 text-[10px]">NH₃-N</TableHead>
                  <TableHead className="h-7 text-[10px]">TSS</TableHead>
                  <TableHead className="h-7 text-[10px]">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[...samples].reverse().slice(0, 30).map((s) => (
                  <TableRow key={s.id} className="border-border/50">
                    <TableCell className="py-1 text-[11px]">{s.sample_date}</TableCell>
                    <TableCell className="py-1 font-mono text-[11px]">
                      {s.bod_bdl ? '<' : ''}{s.bod ?? '—'}
                    </TableCell>
                    <TableCell className="py-1 font-mono text-[11px]">
                      {s.cod_bdl ? '<' : ''}{s.cod ?? '—'}
                    </TableCell>
                    <TableCell className="py-1 font-mono text-[11px]">
                      {s.nh3n_bdl ? '<' : ''}{s.nh3n ?? '—'}
                    </TableCell>
                    <TableCell className="py-1 font-mono text-[11px]">
                      {s.tss_bdl ? '<' : ''}{s.tss ?? '—'}
                    </TableCell>
                    <TableCell
                      className={`py-1 text-[11px] ${
                      s.compliance === 'Not Comply' ? 'text-destructive' : 'text-muted-foreground'
                    }`}
                  >
                      {s.compliance ? `Reported ${s.compliance}` : '—'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </Card>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-muted/50 p-2">
      <div className="text-[10px] text-muted-foreground uppercase">{label}</div>
      <div className="mt-0.5 text-base font-semibold">{value}</div>
    </div>
  )
}

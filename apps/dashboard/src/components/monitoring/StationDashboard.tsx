import { useMemo, useState, type ReactNode } from 'react'
import ReactECharts from '../dashboard/Chart'
import { ArrowRight, FlaskConical } from 'lucide-react'

import { useSamples, useSampleYears, type SampleFilters } from '@/api/monitoring'
import { SAMPLE_METRICS, type Station } from '@/api/monitoring-types'
import { CHART } from '@/components/dashboard/chartPalette'
import { summarizeMetric } from './sampleSummary'
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
  onOpenWorkspace?: () => void
}) {
  const [year, setYear] = useState<SampleFilters['year']>('all')
  const [compliance, setCompliance] = useState<SampleFilters['compliance']>('all')
  const [metric, setMetric] = useState('bod')

  const { data: years } = useSampleYears(station.code)
  const { data: samples, isLoading, isError, refetch } = useSamples(station.code, { year, compliance })

  const orderedSamples = useMemo(() => [...(samples ?? [])].sort((a, b) =>
    (a.sample_date || '').localeCompare(b.sample_date || '')), [samples])
  const latest = orderedSamples.filter(sample => /^\d{4}-\d{2}-\d{2}$/.test(sample.sample_date ?? '')).at(-1)
  const latestValue = latest?.[metric as keyof typeof latest]
  const latestBdl = latest?.[`${metric}_bdl` as keyof typeof latest]
  const meta = SAMPLE_METRICS[metric]
  const stats = useMemo(() => {
    if (!samples?.length) return null
    const reportedStatuses = samples.filter((s) => s.compliance === 'Comply' || s.compliance === 'Not Comply')
    const complyCount = reportedStatuses.filter((s) => s.compliance === 'Comply').length
    return {
      ...summarizeMetric(samples, metric),
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
        <p className="mt-3 text-xs text-muted-foreground">Laboratory observations · historical records, not live plant status.</p>
        {!isLoading && !isError && <div className="mt-3 border-t pt-3 text-sm">
          <p className="font-medium">Latest available sample in this selection</p>
          <p className="mt-1">{latest ? <time dateTime={latest.sample_date}>{latest.sample_date}</time> : 'Observation date unavailable'}</p>
          <p className="mt-2 text-xs">Latest {meta.label} result: {latestBdl ? `Below detection limit${typeof latestValue === 'number' ? ` (<${latestValue} ${meta.unit})` : ' (limit not recorded)'}` : typeof latestValue === 'number' && Number.isFinite(latestValue) ? `${latestValue} ${meta.unit}` : 'Not recorded'}</p>
          <p className="mt-1 text-xs text-muted-foreground">{latest?.sample_point || 'Sampling point not recorded'} · Source dataset year: {latest?.source_year ?? 'not recorded'}</p>
          <p className="mt-1 text-xs text-muted-foreground">Source: imported laboratory dataset. Collection date does not indicate a current operating condition.</p>
        </div>}
      </Card>

      <div className="space-y-3 px-1">
          <div>
            <label id="monitoring-parameter-label" className="mb-1 block text-xs font-medium text-muted-foreground">Parameter</label>
            <ShadSelect value={metric} onValueChange={setMetric}>
              <SelectTrigger aria-labelledby="monitoring-parameter-label" className="h-8 min-h-11 w-full border-border bg-muted text-sm sm:min-h-8">
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
          <details className="text-xs text-muted-foreground">
            <summary className="cursor-pointer py-2">Understand these measurements</summary>
            <dl className="space-y-2 pt-2">
              <div><dt className="font-medium">BOD / COD</dt><dd>Biochemical / chemical oxygen demand: oxygen needed to break down material in the sample.</dd></div>
              <div><dt className="font-medium">TSS</dt><dd>Total suspended solids: particles suspended in the water.</dd></div>
              <div><dt className="font-medium">NH₃-N / NO₃-N</dt><dd>Ammoniacal nitrogen / nitrate nitrogen, expressed as nitrogen.</dd></div>
              <div><dt className="font-medium">Oil &amp; Grease</dt><dd>Material measured by the laboratory's oil-and-grease analysis; interpret with its sampling and analytical method.</dd></div>
              <div><dt className="font-medium">pH / Temperature</dt><dd>pH describes acidity or alkalinity; temperature describes how warm the sample was. Interpret both with sampling context and applicable limits.</dd></div>
              <div><dt className="font-medium">mg/L</dt><dd>Milligrams per litre, a concentration. pH is unitless; temperature is in degrees Celsius.</dd></div>
              <div><dt className="font-medium">Below detection limit (BDL)</dt><dd>The laboratory could not quantify a value below its reported detection limit. This does not mean zero.</dd></div>
            </dl>
          </details>
          <p className="text-xs text-muted-foreground">
            Status is reported by the source dataset. No station-specific permit limits are
            configured, so these charts do not determine legal compliance.
          </p>
      </div>
      <Disclosure title={`Filter records · ${year === 'all' ? 'All years' : year} · ${compliance === 'all' ? 'All statuses' : compliance}`}>
        <div className="space-y-4">
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
        </div>
      </Disclosure>

      {isError && (
        <div role="alert" className="rounded border border-destructive p-3 text-sm">
          <p>Laboratory results are unavailable. Your filters have been kept.</p>
          <Button className="mt-2" onClick={() => void refetch()}>Retry laboratory results</Button>
        </div>
      )}

      {stats && !isError && (
        <Disclosure title={`${meta.label} Summary`}>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <Stat label="Samples" value={String(stats.totalCount)} />
            <Stat
              label="Dataset-reported comply"
              value={stats.reportedComplyPct == null ? '—' : `${stats.reportedComplyPct.toFixed(0)}%`}
            />
            <Stat label={`Mean ${meta.label}`} value={stats.mean == null ? '—' : `${stats.mean.toFixed(1)} ${meta.unit}`} />
            <Stat label={`Max ${meta.label}`} value={stats.max == null ? '—' : `${stats.max.toFixed(1)} ${meta.unit}`} />
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            {stats.quantifiedCount === 0 ? 'No quantifiable readings. ' : ''}
            {stats.quantifiedCount} of {stats.totalCount} samples have quantified {meta.label} readings.
            {' '}Mean and maximum exclude missing and below-detection results; no values are substituted.
          </p>
        </Disclosure>
      )}

      <Card title={`${meta.label} Trend (lab results)`}>
        <p className="mb-3 text-xs text-muted-foreground">Missing and below-detection results appear as gaps, not zero. Points show individual laboratory samples; lines connect observations, not continuous monitoring.</p>
        {isError ? (
          <p className="text-xs text-muted-foreground">Retry laboratory results to view the trend.</p>
        ) : isLoading ? (
          <p className="text-xs text-muted-foreground">Loading samples…</p>
        ) : !samples?.length ? (
          <p className="text-xs text-muted-foreground">No samples match the current filters.</p>
        ) : (
          <ReactECharts
            notMerge
            style={{ height: 220 }}
            option={{
              backgroundColor: 'transparent',
              grid: { left: 48, right: 12, top: 30, bottom: 28 },
              tooltip: { trigger: 'axis' },
              xAxis: {
                type: 'category',
                data: orderedSamples.map((s) => s.sample_date),
                axisLabel: { color: CHART.axis, fontSize: 11 },
                axisLine: { lineStyle: { color: CHART.grid } },
              },
              yAxis: {
                type: 'value',
                scale: true,
                name: meta.unit || 'pH (unitless)',
                axisLabel: { color: CHART.axis, fontSize: 11 },
                splitLine: { lineStyle: { color: CHART.grid } },
              },
              series: [
                {
                  type: 'line',
                  data: orderedSamples.map((s) =>
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



      {!!samples?.length && !isError && (
        <Disclosure title="Recent Samples">
          <div className="max-h-64 overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-border">
                  <TableHead className="h-7 text-[10px]">Date</TableHead>
                  <TableHead className="h-7 text-[10px]">BOD (mg/L)</TableHead>
                  <TableHead className="h-7 text-[10px]">COD (mg/L)</TableHead>
                  <TableHead className="h-7 text-[10px]">NH₃-N (mg/L)</TableHead>
                  <TableHead className="h-7 text-[10px]">TSS (mg/L)</TableHead>
                  <TableHead className="h-7 text-[10px]">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[...orderedSamples].reverse().slice(0, 30).map((s) => (
                  <TableRow key={s.id} className="border-border/50">
                    <TableCell className="py-1 text-[11px]">{s.sample_date || 'Date unavailable'}</TableCell>
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
        </Disclosure>
      )}
      <Disclosure title="Methods and research">
        <p className="text-xs text-muted-foreground">
          Not estimated from these lab samples. The available BOD and nitrogen values are effluent
          measurements; the cited calculation requires influent measurements and plant operating data.
        </p>

        <p className="text-xs text-muted-foreground">Explore assumptions separately from these measured observations. Simulations are illustrative and unvalidated.</p>
        {onOpenWorkspace ? <Button className="mt-3 flex items-center gap-2" onClick={onOpenWorkspace}>
          Research sandbox <ArrowRight className="size-3.5" />
        </Button> : <p className="mt-2 text-xs text-muted-foreground">No linked treatment plant. Research is unavailable for this sampling location.</p>}
      </Disclosure>
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

function Disclosure({ title, children }: { title: string; children: ReactNode }) {
  return <details className="rounded-lg border border-border bg-background p-4">
    <summary className="min-h-6 cursor-pointer text-sm font-semibold">{title}</summary>
    <div className="mt-4">{children}</div>
  </details>
}

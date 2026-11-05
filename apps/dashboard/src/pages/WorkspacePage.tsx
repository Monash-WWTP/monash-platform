import { lazy, Suspense, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ChevronDown, Factory } from 'lucide-react'

import { usePlant, useRun, useTimeseries } from '../api/hooks'
import { useWorkspaceStore } from '../stores/scenarioStore'
import ResultsPanel from '../components/results/ResultsPanel'
import ScenarioPanel from '../components/scenario/ScenarioPanel'
import OperatorHeader from '../components/OperatorHeader'
import { Button } from '../components/ui'
const ComparisonView = lazy(() => import('../components/comparison/ComparisonView'))
const TrendsChart = lazy(() => import('../components/dashboard/TrendsChart'))

export default function WorkspacePage() {
  const { plantId } = useParams()
  const id = Number(plantId)
  const { data: plant, isLoading, isError, refetch } = usePlant(id)
  const { centerTab, setCenterTab, activeRunId, resetWorkspace } =
    useWorkspaceStore()
  const { data: run } = useRun(activeRunId)
  const completedForPlant = run?.plant_id === id && run.status === 'completed'
  const timeseries = useTimeseries(completedForPlant ? activeRunId : null)
  const ts = timeseries.data

  // fresh workspace state when switching plants
  useEffect(() => {
    resetWorkspace()
  }, [id, resetWorkspace])

  if (isLoading) {
    return <div className="flex h-full flex-col"><OperatorHeader context="Simulation lab" /><p role="status" className="p-6 text-sm text-muted-foreground">Loading plant…</p></div>
  }
  if (isError) {
    return <div className="flex h-full flex-col"><OperatorHeader context="Simulation lab" />
      <div role="alert" className="mx-auto max-w-xl space-y-4 p-6">
        <h1 className="text-2xl font-semibold">Plant information is unavailable</h1>
        <p className="text-sm text-muted-foreground">We couldn’t load this plant. Retry, or return to monitoring to select another plant.</p>
        <Button className="min-h-11" onClick={() => void refetch()}>Retry plant</Button>
      </div>
    </div>
  }
  if (!plant) {
    return (
      <div className="flex h-full flex-col gap-4 text-muted-foreground">
        <OperatorHeader context="Simulation lab" />
        Plant not found.
        <Link to="/dashboard" className="text-primary underline">
          Back to map
        </Link>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto lg:overflow-hidden">
      <OperatorHeader context="Simulation lab" />
      <div className="flex shrink-0 flex-wrap items-start justify-between gap-x-4 gap-y-2 border-b border-border bg-background px-4 py-2">
        <details className="group min-w-0 flex-1">
          <summary className="flex min-h-11 cursor-pointer list-none items-center gap-3 rounded focus-visible:outline-2 focus-visible:outline-primary [&::-webkit-details-marker]:hidden">
            <Factory className="size-5 shrink-0 text-primary" />
            <h1 className="min-w-0 text-sm font-semibold [overflow-wrap:anywhere]">{plant.name}</h1>
            <span className="ml-1 text-xs text-muted-foreground">Details</span>
            <ChevronDown className="size-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-180" />
          </summary>
          <div className="max-w-xl space-y-2 pb-3 pt-2 text-xs text-muted-foreground">
            <p>Configured capacity {plant.capacity_mld} MLD · {plant.description}</p>
            <p>Research sandbox · illustrative, unvalidated simulations. Observations remain in monitoring.</p>
            <div className="flex flex-wrap gap-x-4 gap-y-2">
              <Link to="/dashboard/simulation" className="text-primary underline">Simulation lab</Link>
              <Link to={`/dashboard?station=${encodeURIComponent(plant.code ?? '')}`} className="text-primary underline">Back to monitoring</Link>
              <Link to="/dashboard/simulation/methods" className="underline underline-offset-4">Methods and sources</Link>
            </div>
          </div>
        </details>

        <nav aria-label="Workspace views" className="flex max-w-full flex-wrap gap-1 rounded-md border border-border bg-muted p-0.5">
          {(
            [
              ['trends', 'Run results'],
              ['compare', 'Compare scenarios'],
            ] as const
          ).map(([tab, label]) => (
            <button
              key={tab}
              aria-pressed={centerTab === tab}
              onClick={() => setCenterTab(tab)}
              className={`min-h-11 rounded px-3 py-2 text-sm font-medium transition-colors ${
                centerTab === tab ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </div>

      <div className={`grid min-w-0 flex-1 grid-cols-1 lg:min-h-0 ${centerTab === 'trends' ? 'lg:grid-cols-[320px_minmax(0,1fr)] xl:grid-cols-[360px_minmax(0,1fr)]' : ''}`}>
        <aside aria-label="Scenario settings" className={`min-h-0 min-w-0 border-b border-border bg-background lg:overflow-y-auto lg:border-b-0 lg:border-r ${centerTab === 'compare' ? 'hidden' : ''}`}>

          <ScenarioPanel key={id} plantId={id} />
        </aside>
        <main className="min-h-[360px] min-w-0 overflow-y-auto p-4 lg:min-h-0">
          <div className="mx-auto max-w-6xl space-y-4">
            <Suspense fallback={<p role="status" className="p-4 text-sm">Loading view…</p>}>
              {centerTab === 'trends' && <>
                <h2 className="text-lg font-semibold">3. Inspect saved results</h2>
                <ResultsPanel plantId={id} />
                {completedForPlant && timeseries.isError ? <div role="alert" className="space-y-3 rounded border border-destructive p-4 text-sm">
                  <p>Chart data is unavailable. Saved results remain available above.</p>
                  <Button onClick={() => void timeseries.refetch()}>Retry chart data</Button>
                </div> : completedForPlant && timeseries.isLoading ? <p role="status">Loading chart data…</p> : ts ? <TrendsChart ts={ts} maintenance={run?.input_snapshot?.maintenance ?? []} /> : <EmptyCenter />}
              </>}
              {centerTab === 'compare' && <><h2 className="text-lg font-semibold">4. Compare scenarios</h2><ComparisonView plantId={id} /></>}
            </Suspense>
          </div>
        </main>
      </div>
    </div>
  )
}

function EmptyCenter() {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center gap-2 rounded border border-dashed p-6 text-center">
      <Factory className="size-10 text-muted-foreground/40" />
      <p className="text-sm text-muted-foreground">
        No completed simulation to chart. Configure a scenario and press{' '}
        <span className="font-semibold text-foreground">Run Simulation</span>.
      </p>
      <p className="max-w-md text-xs text-muted-foreground/70">
        Illustrative effluent estimates (BOD, COD, TSS, ammonia, nitrate, phosphorus, turbidity, pH)
        will be charted here against configured screening thresholds and maintenance windows.
      </p>
    </div>
  )
}

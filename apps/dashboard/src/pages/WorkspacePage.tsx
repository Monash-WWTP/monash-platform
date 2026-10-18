import { lazy, Suspense, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Factory } from 'lucide-react'

import { usePlant, useTimeseries } from '../api/hooks'
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
  const { centerTab, setCenterTab, activeRunId, draft, resetDraft, setActiveRunId } =
    useWorkspaceStore()
  const { data: ts } = useTimeseries(activeRunId)

  // fresh workspace state when switching plants
  useEffect(() => {
    resetDraft()
    setActiveRunId(null)
  }, [id, resetDraft, setActiveRunId])

  if (isLoading) {
    return <div className="flex h-full flex-col"><OperatorHeader context="Workspace" /><p role="status" className="p-6 text-sm text-muted-foreground">Loading plant…</p></div>
  }
  if (isError) {
    return <div className="flex h-full flex-col"><OperatorHeader context="Workspace" />
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
        <OperatorHeader context="Workspace" />
        Plant not found.
        <Link to="/dashboard" className="text-primary underline">
          Back to map
        </Link>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto lg:overflow-hidden">
      <OperatorHeader context="Workspace" />
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-4 border-b border-border bg-card px-4 py-3">
        <div className="flex min-w-0 items-center gap-3">
          <Factory className="size-5 text-primary" />
          <div className="min-w-0">
            <h1 className="text-sm font-semibold leading-tight [overflow-wrap:anywhere]">{plant.name}</h1>
            <p className="text-[11px] text-muted-foreground leading-tight">
              Configured capacity {plant.capacity_mld} MLD · {plant.description}
            </p>
          </div>
        </div>

        <nav aria-label="Workspace views" className="flex max-w-full flex-wrap gap-1 rounded-md border border-border bg-muted p-0.5">
          {(
            [
              ['trends', 'Effluent Trends'],
              ['compare', 'Scenario Comparison'],
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

      <div className="grid min-w-0 flex-1 grid-cols-1 lg:min-h-0 lg:grid-cols-[300px_minmax(0,1fr)_280px] xl:grid-cols-[330px_minmax(0,1fr)_320px]">
        <aside aria-label="Scenario settings" className="min-h-0 min-w-0 border-b border-border bg-background lg:border-b-0 lg:border-r">
          <ScenarioPanel plantId={id} />
        </aside>

        <main className="min-h-[360px] min-w-0 overflow-y-auto p-3 lg:min-h-0">
          <Suspense fallback={<p role="status" className="p-4 text-sm">Loading view…</p>}>
          {centerTab === 'trends' &&
            (ts ? (
              <TrendsChart ts={ts} maintenance={draft.maintenance} />
            ) : (
              <EmptyCenter />
            ))}
          {centerTab === 'compare' && <ComparisonView plantId={id} />}
          </Suspense>
        </main>

        <aside aria-label="Simulation results" className="min-h-0 min-w-0 border-t border-border bg-background lg:border-l lg:border-t-0">
          <ResultsPanel />
        </aside>
      </div>
    </div>
  )
}

function EmptyCenter() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
      <Factory className="size-10 text-muted-foreground/40" />
      <p className="text-sm text-muted-foreground">
        No simulation yet. Configure a scenario and press{' '}
        <span className="font-semibold text-foreground">Run Simulation</span>.
      </p>
      <p className="max-w-md text-xs text-muted-foreground/70">
        Illustrative effluent estimates (BOD, COD, TSS, ammonia, nitrate, phosphorus, turbidity, pH)
        will be charted here against configured screening thresholds and maintenance windows.
      </p>
    </div>
  )
}

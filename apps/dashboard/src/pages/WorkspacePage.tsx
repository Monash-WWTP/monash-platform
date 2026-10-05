import { useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Factory } from 'lucide-react'

import { usePlant, useTimeseries } from '../api/hooks'
import { useWorkspaceStore } from '../stores/scenarioStore'
import ComparisonView from '../components/comparison/ComparisonView'
import TrendsChart from '../components/dashboard/TrendsChart'
import ResultsPanel from '../components/results/ResultsPanel'
import ScenarioPanel from '../components/scenario/ScenarioPanel'
import DigitalTwin from '../components/twin/DigitalTwin'

export default function WorkspacePage() {
  const { plantId } = useParams()
  const id = Number(plantId)
  const { data: plant, isLoading } = usePlant(id)
  const { centerTab, setCenterTab, activeRunId, draft, resetDraft, setActiveRunId } =
    useWorkspaceStore()
  const { data: ts } = useTimeseries(activeRunId)

  // fresh workspace state when switching plants
  useEffect(() => {
    resetDraft()
    setActiveRunId(null)
  }, [id, resetDraft, setActiveRunId])

  if (isLoading) {
    return <div className="flex h-full items-center justify-center text-muted-foreground">Loading plant…</div>
  }
  if (!plant) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
        Plant not found.
        <Link to="/dashboard" className="text-primary underline">
          Back to map
        </Link>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b border-border bg-card px-4 py-2.5">
        <div className="flex items-center gap-3">
          <Link to="/dashboard" className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="size-4" /> Map
          </Link>
          <div className="h-5 w-px bg-border" />
          <Factory className="size-5 text-primary" />
          <div>
            <h1 className="text-sm font-semibold leading-tight">{plant.name}</h1>
            <p className="text-[11px] text-muted-foreground leading-tight">
              Configured capacity {plant.capacity_mld} MLD · {plant.description}
            </p>
          </div>
        </div>

        <nav className="flex gap-1 rounded-md border border-border bg-muted p-0.5">
          {(
            [
              ['trends', 'Effluent Trends'],
              ['twin', '3D Digital Twin'],
              ['compare', 'Scenario Comparison'],
            ] as const
          ).map(([tab, label]) => (
            <button
              key={tab}
              onClick={() => setCenterTab(tab)}
              className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                centerTab === tab ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-[330px_1fr_320px]">
        <aside className="min-h-0 border-r border-border bg-background">
          <ScenarioPanel plantId={id} />
        </aside>

        <main className="min-h-0 overflow-y-auto p-3">
          {centerTab === 'trends' &&
            (ts ? (
              <TrendsChart ts={ts} maintenance={draft.maintenance} />
            ) : (
              <EmptyCenter />
            ))}
          {centerTab === 'twin' && <DigitalTwin plant={plant} ts={ts ?? null} />}
          {centerTab === 'compare' && <ComparisonView plantId={id} />}
        </main>

        <aside className="min-h-0 border-l border-border bg-background">
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
        No simulation yet. Configure a scenario on the left and press{' '}
        <span className="font-semibold text-foreground">Run Simulation</span>.
      </p>
      <p className="max-w-md text-xs text-muted-foreground/70">
        Illustrative effluent estimates (BOD, COD, TSS, ammonia, nitrate, phosphorus, turbidity, pH)
        will be charted here against configured screening thresholds and maintenance windows.
      </p>
    </div>
  )
}

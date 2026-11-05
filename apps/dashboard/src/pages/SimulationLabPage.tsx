import { Link } from 'react-router-dom'
import { usePlants } from '../api/hooks'
import { useStations } from '../api/monitoring'
import OperatorHeader from '../components/OperatorHeader'

export default function SimulationLabPage() {
  const plants = usePlants()
  const stations = useStations()
  return <div className="flex h-full flex-col overflow-y-auto bg-background">
    <OperatorHeader context="Simulation lab" />
    <main className="mx-auto w-full max-w-3xl space-y-8 px-5 py-8">
      <div>
        <Link to="/dashboard" className="text-sm text-primary underline underline-offset-4">Back to monitoring</Link>
        <h1 className="mt-4 text-2xl font-semibold">Simulation lab</h1>
        <p className="mt-2 text-sm text-muted-foreground">Choose a configured plant to explore scenarios, saved runs and comparisons.</p>
      </div>
      <section aria-label="Available simulation workspaces" className="space-y-3">
        {plants.isLoading && <p role="status">Loading workspaces…</p>}
        {plants.isError && <button onClick={() => void plants.refetch()} className="min-h-11 text-primary underline">Retry workspaces</button>}
        {plants.data?.map(plant => <Link key={plant.id} to={`/dashboard/plants/${plant.id}`}
          className="block rounded-lg border border-border p-5 hover:bg-muted focus-visible:outline-2 focus-visible:outline-primary">
          <h2 className="font-semibold">{plant.code === 'DEMO001' ? 'Demo simulation' : plant.name}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{plant.code === 'DEMO001'
            ? 'Synthetic plant with editable assumptions. Open the saved baseline to start.'
            : `${plant.code ?? plant.name} · Configured capacity ${plant.capacity_mld} MLD`}</p>
          <span className="mt-3 inline-block text-sm font-medium text-primary">Open lab →</span>
        </Link>)}
        {plants.data?.length === 0 && <p>No configured simulation plants yet.</p>}
      </section>
      <section aria-label="Imported location readiness" className="border-t border-border pt-6">
        <h2 className="font-semibold">Imported locations</h2>
        <p className="mt-2 text-sm text-muted-foreground">Final-effluent results support monitoring. Site-specific simulation also needs influent flow and composition, design capacity, equipment availability and maintenance assumptions.</p>
        {stations.isLoading && <p role="status" className="mt-3 text-sm">Loading locations…</p>}
        {stations.isError && <button onClick={() => void stations.refetch()} className="min-h-11 text-sm text-primary underline">Retry imported locations</button>}
        <ul className="mt-3 divide-y divide-border">
          {stations.data?.map(station => {
            const plant = plants.data?.find(item => item.code === station.code)
            return <li key={station.code} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm">
              <Link className="text-primary underline underline-offset-4" to={`/dashboard?station=${encodeURIComponent(station.code)}`}>{station.name}</Link>
              {plant ? <Link className="text-primary underline" to={`/dashboard/plants/${plant.id}`}>Open lab</Link>
                : <span className="text-muted-foreground">Engineering inputs not configured</span>}
            </li>
          })}
        </ul>
      </section>
      <p className="text-xs text-muted-foreground">Research sandbox · illustrative, unvalidated outputs. Laboratory measurements remain separate from scenario assumptions.</p>
    </main>
  </div>
}

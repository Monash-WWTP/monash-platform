import { Link } from 'react-router-dom'
import OperatorHeader from '../components/OperatorHeader'
import MethodsPanel from '../components/research/MethodsPanel'

export default function SimulationMethodsPage() {
  return <div className="flex h-full flex-col overflow-y-auto bg-background">
    <OperatorHeader context="Methods and sources" />
    <main className="mx-auto w-full max-w-4xl space-y-5 px-5 py-8">
      <Link to="/dashboard/simulation" className="inline-flex min-h-11 items-center text-sm text-primary underline">Back to Simulation lab</Link>
      <MethodsPanel expanded />
    </main>
  </div>
}

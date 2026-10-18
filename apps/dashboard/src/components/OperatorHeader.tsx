import { Link } from 'react-router-dom'

/** Shared navigation for the monitoring, scenario and review surfaces. */
export default function OperatorHeader({ context, monitoring = false }: { context: string; monitoring?: boolean }) {
  return <header className="flex min-h-14 shrink-0 flex-wrap items-center justify-between gap-x-5 gap-y-2 border-b border-border bg-background px-4 py-3">
    <Link to="/" className="text-lg font-bold tracking-tight text-foreground">Monash Water</Link>
    <nav aria-label="Operator navigation" className="flex flex-wrap items-center gap-4 text-sm">
      {!monitoring && <Link to="/dashboard" className="text-primary underline underline-offset-4">Monitoring</Link>}
      <span aria-current="page">{context}</span>
    </nav>
  </header>
}

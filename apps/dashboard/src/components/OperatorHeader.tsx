import { Link } from 'react-router-dom'
import { documentationUrl, documentationLabel } from '../lib/documentation'

/** Shared navigation for the monitoring, scenario and review surfaces. */
export default function OperatorHeader({ context, monitoring = false }: { context: string; monitoring?: boolean }) {
  return <header className="flex min-h-14 shrink-0 flex-wrap items-center justify-between gap-x-5 gap-y-2 border-b border-border bg-background px-4 py-3">
    <Link to="/" className="text-lg font-bold tracking-tight text-foreground">Monash Water</Link>
    <nav aria-label="Operator navigation" className="flex flex-wrap items-center gap-4 text-sm">
      {!monitoring && <Link to="/dashboard" className="text-primary underline underline-offset-4">Monitoring</Link>}
      {context !== 'Operations reports' && <Link to="/dashboard/operations" className="text-primary underline underline-offset-4">Operations reports</Link>}
      {context !== 'Report review' && <Link to="/dashboard/moderation" className="text-primary underline underline-offset-4">Publication review</Link>}
      {context !== 'Administration' && <Link to="/dashboard/admin" className="text-primary underline underline-offset-4">Administration</Link>}
      <a href={documentationUrl} className="text-primary underline underline-offset-4">{documentationLabel}</a>
      <span aria-current="page">{context}</span>
    </nav>
  </header>
}

import { Link } from 'react-router-dom'

/** Quiet shared header; task navigation belongs within each operator surface. */
export default function OperatorHeader({ context }: { context: string; monitoring?: boolean }) {
  return <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-background px-4">
    <Link to="/" aria-label="Monash Water home" className="rounded focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary">
      <img src="/assets/platform-logo.png" alt="Monash Water" className="size-8" />
    </Link>
    <nav aria-label="Operator navigation">
      <Link to="/" className="inline-flex min-h-11 items-center text-sm text-muted-foreground hover:text-foreground">Back to main page</Link>
    </nav>
    <span className="sr-only" aria-current="page">{context}</span>
  </header>
}

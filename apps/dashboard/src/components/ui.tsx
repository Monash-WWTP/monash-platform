/* Project-level wrappers over shadcn/ui primitives (src/components/ui/). */
import type { ReactNode } from 'react'

import { Badge as ShadBadge } from '@/components/ui/badge'
import { Button as ShadButton } from '@/components/ui/button'
import {
  Card as ShadCard,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input as ShadInput } from '@/components/ui/input'
import { cn } from '@/lib/utils'

export { Slider } from '@/components/ui/slider'
export {
  Select as ShadSelect,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
export { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
export {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export function Card({
  title,
  children,
  className,
  action,
}: {
  title?: string
  children: ReactNode
  className?: string
  action?: ReactNode
}) {
  return (
    <ShadCard className={cn('gap-0 rounded-lg border-border bg-card py-0', className)}>
      {title && (
        <CardHeader className="flex-row items-center justify-between border-b border-border px-3 !py-2">
          <CardTitle className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
            {title}
          </CardTitle>
          {action}
        </CardHeader>
      )}
      <CardContent className="p-3">{children}</CardContent>
    </ShadCard>
  )
}

export function Label({ children }: { children: ReactNode }) {
  return <label className="mb-1 block text-xs font-medium text-muted-foreground">{children}</label>
}

export function Input(props: React.ComponentProps<typeof ShadInput>) {
  return (
    <ShadInput
      {...props}
      className={cn('h-8 border-border bg-muted text-sm text-foreground', props.className)}
    />
  )
}

/** Native select kept for simple forms; shadcn Select also exported above. */
export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={cn(
        'w-full rounded-md border border-border bg-muted px-2.5 py-1.5 text-sm text-foreground',
        'focus:border-primary focus:outline-none',
        props.className,
      )}
    />
  )
}

export function Button({
  variant = 'default',
  className,
  ...props
}: React.ComponentProps<'button'> & {
  variant?: 'default' | 'primary' | 'danger' | 'ghost'
}) {
  const map = {
    primary: { v: 'default' as const, cls: 'bg-primary text-primary-foreground hover:bg-primary/85' },
    default: { v: 'outline' as const, cls: 'border-border bg-muted text-foreground hover:bg-accent hover:text-foreground' },
    danger: { v: 'outline' as const, cls: 'border-destructive/40 bg-destructive/10 text-destructive hover:bg-destructive/20 hover:text-destructive' },
    ghost: { v: 'ghost' as const, cls: 'text-muted-foreground hover:bg-muted hover:text-foreground' },
  }[variant]
  return <ShadButton variant={map.v} size="sm" className={cn(map.cls, className)} {...props} />
}

export function SegmentGroup<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string }[]
  value: T
  onChange: (v: T) => void
}) {
  return (
    <div className="flex w-full rounded-md border border-border bg-muted p-0.5">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={cn(
            'flex-1 rounded px-2 py-1 text-xs font-medium transition-colors',
            value === opt.value
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground',
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

const severityColor: Record<string, string> = {
  low: 'text-emerald-700 bg-emerald-50 border-emerald-300',
  medium: 'text-amber-700 bg-amber-50 border-amber-300',
  high: 'text-destructive bg-destructive/10 border-destructive/30',
}

export function Badge({ severity, children }: { severity: string; children: ReactNode }) {
  return (
    <ShadBadge
      variant="outline"
      className={cn(
        'rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide',
        severityColor[severity] ?? 'border-border text-muted-foreground',
      )}
    >
      {children}
    </ShadBadge>
  )
}

export function Spinner() {
  return (
    <div className="size-4 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-primary" />
  )
}

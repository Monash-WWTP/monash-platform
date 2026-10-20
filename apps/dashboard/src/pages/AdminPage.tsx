import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAccount } from '../api/accounts'
import { adminApi, ordinaryCapabilities, capabilityLabels, type AdminUser, type PlantSettings, type AdminStation, newPlant } from '../api/admin'
import type { Page } from '../api/transport'
import OperatorHeader from '../components/OperatorHeader'
import OperatorAccess from '../components/auth/OperatorAccess'
import { Button, Input } from '../components/ui'
import { PlantForm, StationForm, Failure, fieldClass } from '../components/admin/SettingsForms'

const views = ['Users', 'Plants', 'Stations', 'History', 'Status'] as const
function Pagination({ page, offset, move }: { page?: Page<unknown>; offset: number; move: (value: number) => void }) {
  if (!page) return null
  return <div className="flex flex-wrap items-center gap-4 border-t border-border pt-4 text-sm"><span>{page.total ? `${offset + 1}–${offset + page.items.length} of ${page.total}` : 'No records'}</span><Button variant="default" disabled={offset === 0} onClick={() => move(Math.max(0, offset - 25))}>Previous</Button><Button variant="default" disabled={offset + page.items.length >= page.total} onClick={() => move(offset + 25)}>Next</Button></div>
}
function QueryState({ loading, error, retry }: { loading: boolean; error: unknown; retry: () => void }) { return <>{loading && <p role="status">Loading…</p>}{error ? <div className="space-y-3"><Failure error={error} /><Button variant="default" onClick={retry}>Retry loading</Button></div> : null}</> }
function PermissionForm({ user, saved }: { user: AdminUser; saved: () => Promise<void> }) {
  const [caps, setCaps] = useState(user.capabilities.filter(c => ordinaryCapabilities.some(v => v === c)))
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)
  async function submit(e: React.FormEvent) { e.preventDefault(); setBusy(true); setError(null); try { await adminApi.permissions(user, caps, reason.trim()); await saved() } catch (e) { setError(e) } finally { setBusy(false) } }
  return <form onSubmit={submit} className="space-y-4 border-t border-border pt-5"><h3 className="font-semibold">Permissions for {user.email}</h3><p className="text-sm text-muted-foreground">A change signs this user out of browser sessions. Platform administrator grants are managed through the server.</p><fieldset disabled={busy} className="space-y-4"><div className="flex flex-wrap gap-5">{ordinaryCapabilities.map(cap => <label key={cap} className="flex min-h-11 items-center gap-2 text-sm"><input type="checkbox" checked={caps.includes(cap)} onChange={e => setCaps(current => e.target.checked ? [...current, cap] : current.filter(v => v !== cap))} />{capabilityLabels[cap]}</label>)}</div><label className={fieldClass}>Change reason<Input required minLength={3} maxLength={1000} value={reason} onChange={e => setReason(e.target.value)} /></label><Failure error={error} /><Button type="submit" variant="primary">{busy ? 'Saving…' : 'Save permissions'}</Button></fieldset></form>
}
function UsersView({ self }: { self: string }) {
  const client = useQueryClient()
  const [q, setQ] = useState('')
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState<AdminUser | null>(null)
  const [notice, setNotice] = useState('')
  const query = useQuery({ queryKey: ['admin', 'users', search, offset], queryFn: () => adminApi.users(search, offset), retry: false })
  async function saved() { setSelected(null); setNotice('Permissions saved. Affected browser sessions were revoked.'); await client.invalidateQueries({ queryKey: ['admin'] }) }
  return <section className="space-y-6"><h2 className="text-xl font-semibold">Users</h2><p className="max-w-2xl text-sm text-muted-foreground">Manage application permissions for registered accounts. Enrollment, invitations, password recovery and account disabling remain in the identity service.</p><form className="flex flex-wrap items-end gap-3" onSubmit={e => { e.preventDefault(); setOffset(0); setSearch(q.trim()); setSelected(null) }}><label className={`${fieldClass} min-w-0 flex-1`}>Search users<Input type="search" value={q} onChange={e => setQ(e.target.value)} placeholder="Email or account ID" /></label><Button type="submit" variant="primary">Search</Button></form><QueryState loading={query.isFetching} error={query.error} retry={() => void query.refetch()} /><p role="status" className="text-sm">{notice}</p>
    <div className="divide-y divide-border">{query.data?.items.map(user => <article key={user.id} className="flex flex-wrap items-center justify-between gap-3 py-4"><div className="min-w-0"><p className="break-words font-medium">{user.email}</p><p className="break-words text-sm text-muted-foreground">{user.capabilities.map(cap => capabilityLabels[cap] ?? cap).join(', ') || 'No application permissions'}</p></div><Button variant="default" disabled={user.id === self} onClick={() => { setSelected(user); setNotice('') }}>{user.id === self ? 'Your account' : 'Edit permissions'}</Button></article>)}</div>
    <Pagination page={query.data} offset={offset} move={value => { setOffset(value); setSelected(null) }} />{selected && <PermissionForm key={selected.id} user={selected} saved={saved} />}
  </section>
}
function PlantsView() {
  const client = useQueryClient()
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState<PlantSettings | null>(null)
  const [generation, setGeneration] = useState(0)
  const [notice, setNotice] = useState('')
  const query = useQuery({ queryKey: ['admin', 'plants', offset], queryFn: () => adminApi.plants(offset), retry: false })
  async function reload() { setSelected(null); setGeneration(v => v + 1); await client.invalidateQueries({ queryKey: ['admin'] }) }
  async function saved() { await reload(); setNotice('Plant configuration saved as a new revision. Existing runs were retained.') }
  return <section className="space-y-6"><h2 className="text-xl font-semibold">Plants</h2><QueryState loading={query.isFetching} error={query.error} retry={() => void query.refetch()} /><p role="status" className="text-sm">{notice}</p><div className="divide-y divide-border">{query.data?.items.map(plant => <article key={plant.id} className="flex flex-wrap items-center justify-between gap-3 py-4"><div className="min-w-0"><p className="break-words font-medium">{plant.name}</p><p className="text-sm text-muted-foreground">{plant.code} · Revision {plant.revision} · {plant.capacity_mld} MLD</p></div><Button variant="default" onClick={() => { setSelected(plant); setNotice('') }}>Edit plant</Button></article>)}</div><Pagination page={query.data} offset={offset} move={setOffset} /><PlantForm key={`${selected?.id ?? 'new'}-${generation}`} initial={selected ?? newPlant()} saved={saved} discard={() => void reload()} /></section>
}
function StationsView() {
  const client = useQueryClient()
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState<AdminStation | null>(null)
  const [generation, setGeneration] = useState(0)
  const [notice, setNotice] = useState('')
  const query = useQuery({ queryKey: ['admin', 'stations', offset], queryFn: () => adminApi.stations(offset), retry: false })
  async function reload() { setSelected(null); setGeneration(v => v + 1); await client.invalidateQueries({ queryKey: ['admin'] }) }
  async function saved() { await reload(); setNotice('Station metadata saved. Historical sample records were retained.') }
  const blank: AdminStation = { code: '', revision: '', payload: { name: '', category: '', stp_type: '', latitude: 0, longitude: 0 } }
  return <section className="space-y-6"><h2 className="text-xl font-semibold">Stations</h2><QueryState loading={query.isFetching} error={query.error} retry={() => void query.refetch()} /><p role="status" className="text-sm">{notice}</p><div className="divide-y divide-border">{query.data?.items.map(station => <article key={station.code} className="flex flex-wrap items-center justify-between gap-3 py-4"><div><p className="font-medium">{station.payload.name}</p><p className="text-sm text-muted-foreground">{station.code}</p></div><Button variant="default" onClick={() => { setSelected(station); setNotice('') }}>Edit station</Button></article>)}</div><Pagination page={query.data} offset={offset} move={setOffset} /><StationForm key={`${selected?.code ?? 'new'}-${generation}`} initial={selected ?? blank} creating={!selected} saved={saved} discard={() => void reload()} /></section>
}
function HistoryView() {
  const [offset, setOffset] = useState(0)
  const query = useQuery({ queryKey: ['admin', 'history', offset], queryFn: () => adminApi.history(offset), retry: false })
  return <section className="space-y-6"><h2 className="text-xl font-semibold">Configuration history</h2><p className="text-sm text-muted-foreground">Administrative changes retain their actor, reason and previous values.</p><QueryState loading={query.isFetching} error={query.error} retry={() => void query.refetch()} /><ol className="divide-y divide-border">{query.data?.items.map(event => <li key={event.id} className="space-y-3 py-5"><p className="font-medium">{event.action} · {event.resource_id}</p><p className="break-words text-sm text-muted-foreground">{new Date(event.created_at).toLocaleString()} · Actor {event.actor_id ?? 'Server administration'}</p><details><summary className="cursor-pointer text-sm text-primary underline underline-offset-4">View change details</summary><pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words rounded border border-border p-3 text-xs">{JSON.stringify(event.details, null, 2)}</pre></details></li>)}</ol><Pagination page={query.data} offset={offset} move={setOffset} /></section>
}
function StatusView() {
  const query = useQuery({ queryKey: ['admin', 'status'], queryFn: adminApi.status, retry: false })
  return <section className="space-y-6"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-semibold">Service status</h2><Button variant="default" onClick={() => void query.refetch()}>Refresh status</Button></div><QueryState loading={query.isFetching} error={query.error} retry={() => void query.refetch()} />{query.data && <><dl className="grid gap-5 border-y border-border py-5 sm:grid-cols-2"><div><dt className="text-sm text-muted-foreground">Environment</dt><dd>{query.data.environment}</dd></div>{Object.entries(query.data.dependencies).map(([key, value]) => <div key={key}><dt className="text-sm capitalize text-muted-foreground">{key}</dt><dd>{value}</dd></div>)}</dl><p className="text-sm">Model {query.data.model.id} · {query.data.model.version} · {query.data.model.validation_status}</p><p className="max-w-2xl text-sm text-muted-foreground">Dependency readiness is a live check, not release acceptance. Backups, recovery, physical-device tests and independent scientific validation require separate evidence.</p><p className="text-sm">Decision use: {query.data.model.decision_use_permitted ? 'Permitted under recorded acceptance' : 'Not permitted'}</p></>}</section>
}
export default function AdminPage() {
  const account = useAccount()
  const [params, setParams] = useSearchParams()
  const requested = params.get('view') ?? 'users'
  const view = views.some(v => v.toLowerCase() === requested) ? requested : 'users'
  const capable = account.data?.capabilities.includes('platform:admin') ?? false
  const access = useQuery({ queryKey: ['admin', 'access'], queryFn: adminApi.status, enabled: capable, retry: false })
  const allowed = capable && !!access.data
  return <div className="min-h-full bg-background text-foreground"><OperatorHeader context="Administration" /><main className="mx-auto max-w-5xl space-y-7 px-4 py-7 sm:px-6"><div><h1 className="text-3xl font-semibold tracking-tight">Platform administration</h1><p className="mt-3 max-w-2xl text-sm text-muted-foreground">Manage access and operational settings with a recorded reason for every change.</p></div><OperatorAccess />{capable && !access.data && <QueryState loading={access.isFetching} error={access.error} retry={() => void access.refetch()} />}{!allowed ? <p role="status">Platform administrator permission and MFA are required. Ask the platform owner to approve access.</p> : <><div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4"><nav aria-label="Administration sections" className="flex flex-wrap gap-2">{views.map(v => <Button key={v} variant={view === v.toLowerCase() ? 'primary' : 'default'} aria-pressed={view === v.toLowerCase()} onClick={() => setParams({ view: v.toLowerCase() })}>{v}</Button>)}</nav><Link to="/dashboard/moderation" className="text-sm text-primary underline underline-offset-4">Review reports</Link></div>{view === 'users' && <UsersView self={account.data!.id} />}{view === 'plants' && <PlantsView />}{view === 'stations' && <StationsView />}{view === 'history' && <HistoryView />}{view === 'status' && <StatusView />}</>}</main></div>
}

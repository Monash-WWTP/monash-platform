import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useAccount, type Account } from '../api/accounts';
import { ApiRequestError, fetchApi, type Page } from '../api/transport';
import { observationSummary, observationPrivateContext } from '../api/observations';
import { stateLabels, type OperationsReport, type OperationsDetail, type RegistryItem, type responseEventBody } from '../api/operator-response';
import OperatorHeader from '../components/OperatorHeader';
import OperatorAccess from '../components/auth/OperatorAccess';
import ResponseForm from '../components/operations/ResponseForm';
import { Button } from '../components/ui';
export default function OperationsReportsPage() {
    const account = useAccount();
    return <OperationsWorkspace key={`${account.data?.id ?? 'anonymous'}:${account.data?.capabilities.join(',') ?? ''}`} account={account.data}/>;
}
function OperationsWorkspace({ account }: {
    account?: Account;
}) {
    const client = useQueryClient();
    const [filter, setFilter] = useState(''), [offset, setOffset] = useState(0), [selected, setSelected] = useState<string | null>(null), [busy, setBusy] = useState(false), [error, setError] = useState(''), [reviewGuards, setReviewGuards] = useState<Record<string, boolean>>({}), [denied, setDenied] = useState(false);
    const allowed = !!account?.capabilities.includes('report:respond') && !denied;
    const scope = account?.id;
    const queue = useQuery({ queryKey: ['operations', scope, filter, offset], queryFn: () => guarded<Page<OperationsReport>>(`/api/v1/operations/reports?offset=${offset}&limit=25${filter ? `&state=${filter}` : ''}`), enabled: allowed, retry: false });
    const detail = useQuery({ queryKey: ['operations-detail', scope, selected], queryFn: () => guarded<OperationsDetail>(`/api/v1/operations/reports/${selected}`), enabled: allowed && !!selected, retry: false });
    const choices = useQuery({ queryKey: ['operations-choices', scope], queryFn: async () => { const [responders, plants, stations] = await Promise.all(['responders', 'plants', 'stations'].map(p => guarded<RegistryItem[]>(`/api/v1/operations/${p}`))); return { responders, plants, stations }; }, enabled: allowed, retry: false });
    const failure = queue.error ?? detail.error ?? choices.error;
    useEffect(() => { if (!allowed)
        client.removeQueries({ predicate: q => String(q.queryKey[0]).startsWith('operations') }); }, [allowed, client]);
    async function guarded<T>(path: string): Promise<T> {
        try {
            return await fetchApi<T>(path);
        }
        catch (e) {
            if (e instanceof ApiRequestError && [401, 403].includes(e.status))
                setDenied(true);
            throw e;
        }
    }
    async function submit(body: ReturnType<typeof responseEventBody>) {
        setBusy(true);
        setError('');
        try {
            const result = await fetchApi<OperationsDetail>(`/api/v1/operations/reports/${selected}/events`, { method: 'POST', body: JSON.stringify(body) });
            client.setQueryData(['operations-detail', scope, selected], result);
            await client.invalidateQueries({ queryKey: ['operations'] });
            return true;
        }
        catch (e) {
            setError(e instanceof Error ? e.message : 'Response could not be confirmed. Reload the case before retrying.');
            if (e instanceof ApiRequestError && [401, 403].includes(e.status))
                setDenied(true);
            else {
                if (selected)
                    setReviewGuards(g => ({ ...g, [selected]: false }));
                await refreshSelected();
            }
            return false;
        }
        finally {
            setBusy(false);
        }
    }
    const stale = selected !== null && Object.hasOwn(reviewGuards, selected);
    const reviewReady = !!selected && reviewGuards[selected] === true && !detail.isFetching && !detail.isError;
    async function refreshSelected() {
        const id = selected;
        const result = await detail.refetch();
        if (id && result.isSuccess)
            setReviewGuards(g => Object.hasOwn(g, id) ? { ...g, [id]: true } : g);
    }
    function acknowledgeReview() { if (selected && reviewReady)
        setReviewGuards(g => { const next = { ...g }; delete next[selected]; return next; }); }
    const d = allowed ? detail.data : undefined;
    return <div className="min-h-full"><OperatorHeader context="Operations reports"/><main className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6"><h1 className="text-2xl font-semibold">Operations reports</h1><OperatorAccess />
 {!allowed ? <p role="status">Response permission and operator sign-in with MFA are required.</p> : <>
 <p className="text-sm text-muted-foreground">Track investigation and response. Public-summary approval remains a separate review.</p>
 {(error || failure) && <div role="alert" className="rounded border border-destructive p-4"><p>{error || failure?.message}</p>{failure && <Button className="mt-3" onClick={() => { void queue.refetch(); void choices.refetch(); if (selected)
            void refreshSelected(); }}>Retry</Button>}</div>}
 <div className="grid gap-8 lg:grid-cols-[minmax(16rem,1fr)_minmax(0,2fr)]"><section aria-label="Reports" className="space-y-3"><label className="block">Response status<select className="ml-3 min-h-11 rounded border border-input bg-background p-2" value={filter} onChange={e => { setFilter(e.target.value); setOffset(0); }}><option value="">All</option>{Object.entries(stateLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
 {queue.isFetching && <p role="status">Loading reports…</p>}{queue.data?.items.length === 0 && <p>No reports in this view.</p>}
 <ul className="divide-y divide-border">{queue.data?.items.map(x => <li key={x.report.id}><button className={`w-full py-4 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary ${selected === x.report.id ? 'text-primary' : ''}`} aria-pressed={selected === x.report.id} onClick={() => { setSelected(x.report.id); setError(''); }}><span className="block font-semibold">{x.report.observation ? observationSummary(x.report.observation).split(':')[0] : `Legacy ${x.report.category}`}</span><span className="block text-sm">{new Date(x.report.observed_at).toLocaleString()} · {stateLabels[x.response.state]}</span></button></li>)}</ul>
 {queue.data && <div className="flex items-center justify-between gap-3"><Button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 25))}>Previous</Button><span className="text-sm">{queue.data.total} reports</span><Button disabled={offset + 25 >= queue.data.total} onClick={() => setOffset(offset + 25)}>Next</Button></div>}</section>
 <section aria-label="Case detail" className="min-w-0 space-y-5 [overflow-wrap:anywhere]">{detail.isFetching && <p role="status">Loading case…</p>}{!selected && <p>Select a report to investigate.</p>}{d && <><h2 className="text-xl font-semibold">{stateLabels[d.response.state]} · revision {d.response.revision}</h2><p>{d.report.observation ? observationSummary(d.report.observation) : `Legacy ${d.report.category}: ${d.report.condition ?? `${d.report.reading_value} ${d.report.reading_unit}`}`}</p><p className="text-sm">{observationPrivateContext(d.report)}</p><dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm"><dt>Observed</dt><dd>{new Date(d.report.observed_at).toLocaleString()}</dd><dt>Submitted</dt><dd>{new Date(d.report.created_at).toLocaleString()}</dd><dt>Private location</dt><dd>{d.report.latitude.toFixed(5)}, {d.report.longitude.toFixed(5)}</dd><dt>Publication</dt><dd>{d.report.moderation_status}</dd><dt>Responsible operator</dt><dd>{choices.data?.responders.find(r => r.id === d.response.assignee_id)?.label ?? d.response.assignee_id ?? 'Unassigned'}</dd><dt>Plant / station</dt><dd>{choices.data?.plants.find(p => p.id === String(d.response.plant_id))?.label ?? d.response.plant_id ?? 'None'} / {d.response.station_code ?? 'None'}</dd></dl>{d.report.note && <p className="whitespace-pre-wrap">{d.report.note}</p>}{d.report.media_id && <a className="inline-block underline" href={`/api/v1/media/${d.report.media_id}`} target="_blank" rel="noreferrer">View private photo</a>}
 <h3 className="text-lg font-semibold">Response history</h3>{d.events.length === 0 ? <p className="text-sm">No response recorded.</p> : <ol className="space-y-4">{d.events.map(e => <li key={e.id} className="border-b border-border pb-3"><p className="font-medium">{e.action} · {new Date(e.created_at).toLocaleString()}</p><p className="text-sm">Recorded by {choices.data?.responders.find(r => r.id === e.actor_id)?.label ?? e.actor_id}</p><p>{e.reason}</p><dl className="mt-2 text-sm">{Object.entries(e.details).map(([k, v]) => <div key={k}><dt className="inline font-medium">{k.replaceAll('_', ' ')}: </dt><dd className="inline">{v === null ? 'Cleared' : String(v)}</dd></div>)}</dl></li>)}</ol>}
 {choices.data && <ResponseForm key={d.report.id} detail={d} {...choices.data} busy={busy} stale={stale} reviewReady={reviewReady} onSubmit={submit} onReview={acknowledgeReview}/>}</>}</section></div></>}
 </main></div>;
}

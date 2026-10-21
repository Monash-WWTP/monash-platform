import { useState } from 'react';
import { Button } from '../ui';
import { actionLabels, responseActions, responseEventBody, type OperationsDetail, type RegistryItem, type ResponseAction } from '../../api/operator-response';
const control = 'mt-1 block min-h-11 w-full rounded border border-input bg-background p-2 text-sm';
export default function ResponseForm({ detail, responders, plants, stations, busy, stale, reviewReady, onSubmit, onReview }: {
    detail: OperationsDetail;
    responders: RegistryItem[];
    plants: RegistryItem[];
    stations: RegistryItem[];
    busy: boolean;
    stale: boolean;
    reviewReady: boolean;
    onSubmit: (body: ReturnType<typeof responseEventBody>) => Promise<boolean>;
    onReview: () => void;
}) {
    const [action, setAction] = useState<ResponseAction>(detail.response.state === 'closed' ? 'reopen' : 'acknowledge');
    const [reason, setReason] = useState(''), [note, setNote] = useState(''), [assignee, setAssignee] = useState(''), [plant, setPlant] = useState(detail.response.plant_id?.toString() ?? ''), [station, setStation] = useState(detail.response.station_code ?? '');
    const [result, setResult] = useState(''), [time, setTime] = useState('');
    const actions = responseActions(detail.response.state);
    const selected = actions.includes(action) ? action : actions[0];
    async function submit(e: React.FormEvent) {
        e.preventDefault();
        const fields: Record<string, unknown> = {};
        if (selected === 'assign')
            fields.assignee_id = assignee;
        if (selected === 'associate') {
            fields.plant_id = plant ? Number(plant) : null;
            fields.station_code = station || null;
        }
        if (['inspect', 'act', 'close'].includes(selected))
            fields.note = note.trim();
        if (selected === 'inspect') {
            fields.result = result;
            fields.observed_at = new Date(time).toISOString();
        }
        if (await onSubmit(responseEventBody(detail.response.revision, selected, reason, fields))) {
            setReason('');
            setNote('');
            setResult('');
            setTime('');
        }
    }
    return <form onSubmit={e => void submit(e)} className="space-y-4 border-t border-border pt-5">
  <h3 className="text-lg font-semibold">Record a response</h3>
  {stale && <div role="alert"><p>This case changed. Review the updated state and history before submitting again. Your text is kept.</p><Button type="button" className="mt-2" disabled={!reviewReady} onClick={onReview}>I reviewed the updated case</Button></div>}
  <fieldset disabled={busy || stale} className="space-y-4 disabled:opacity-60">
   <label className="block">Action<select className={control} value={selected} onChange={e => setAction(e.target.value as ResponseAction)}>{actions.map(a => <option key={a} value={a}>{actionLabels[a]}</option>)}</select></label>
   {selected === 'assign' && <label className="block">Responsible operator<select required className={control} value={assignee} onChange={e => setAssignee(e.target.value)}><option value="">Select operator</option>{responders.map(r => <option key={r.id} value={r.id}>{r.label}</option>)}</select></label>}
   {selected === 'associate' && <><label className="block">Plant<select className={control} value={plant} onChange={e => setPlant(e.target.value)}><option value="">No plant linked</option>{plants.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}</select></label><label className="block">Station<select className={control} value={station} onChange={e => setStation(e.target.value)}><option value="">No station linked</option>{stations.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}</select></label><p className="text-sm text-muted-foreground">Association records investigation context; it does not establish a cause.</p></>}
   {selected === 'inspect' && <><label className="block">Inspection result<select required className={control} value={result} onChange={e => setResult(e.target.value)}><option value="">Select result</option><option value="confirmed">Confirmed</option><option value="not_confirmed">Not confirmed</option><option value="unable_to_verify">Unable to verify</option></select></label><label className="block">Inspected at (your local time)<input required type="datetime-local" className={control} value={time} onChange={e => setTime(e.target.value)}/></label><p className="text-sm text-muted-foreground">Record method and evidence below. Inspection confirmation is separate from scientific validation.</p></>}
   {['inspect', 'act', 'close'].includes(selected) && <label className="block">{selected === 'inspect' ? 'Method and evidence' : selected === 'close' ? 'Disposition' : 'Action taken'}<textarea required minLength={3} maxLength={2000} className={control + ' min-h-24'} value={note} onChange={e => setNote(e.target.value)}/></label>}
   <label className="block">Reason<textarea required minLength={3} maxLength={1000} className={control + ' min-h-20'} value={reason} onChange={e => setReason(e.target.value)}/></label>
   <Button type="submit" variant="primary" className="min-h-11">{busy ? 'Saving…' : actionLabels[selected]}</Button>
  </fieldset>
 </form>;
}

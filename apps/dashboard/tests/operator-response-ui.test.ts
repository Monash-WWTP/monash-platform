import test from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { createElement, act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import OperationsReportsPage from '../src/pages/OperationsReportsPage';
test('failed refresh and same-row selection cannot bypass explicit case review', async () => {
    const dom = new JSDOM('<div id="root"></div>', { url: 'http://localhost/dashboard/operations' });
    const names = ['window', 'document', 'navigator', 'IS_REACT_ACT_ENVIRONMENT'] as const;
    const previous = new Map(names.map(n => [n, Object.getOwnPropertyDescriptor(globalThis, n)]));
    for (const [name, value] of Object.entries({ window: dom.window, document: dom.window.document, navigator: dom.window.navigator, IS_REACT_ACT_ENVIRONMENT: true }))
        Object.defineProperty(globalThis, name, { value, configurable: true, writable: true });
    const account = { id: 'operator', email: 'qa@example.test', capabilities: ['report:respond'] };
    const report = { id: 'case', observation: { kind: 'flooding', response: 'unknown' }, observed_at: '2026-10-01T12:00:00Z', created_at: '2026-10-01T12:01:00Z', latitude: 3, longitude: 101, moderation_status: 'pending' };
    const detail = { report, response: { revision: 0, state: 'unassigned', assignee_id: null, plant_id: null, station_code: null, updated_at: null }, events: [] };
    let failed = false, refreshOK = false;
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (url, init) => {
        const path = String(url);
        if (init?.method === 'POST') {
            failed = true;
            return new Response(JSON.stringify({ error: { message: 'Case changed' } }), { status: 409 });
        }
        if (path.endsWith('/auth/me'))
            return Response.json(account);
        if (path.includes('/reports?'))
            return Response.json({ items: [detail], total: 1, offset: 0, limit: 25 });
        if (path.endsWith('/reports/case'))
            return failed && !refreshOK ? new Response(JSON.stringify({ error: { message: 'Unavailable' } }), { status: 503 }) : Response.json(detail);
        return Response.json([]);
    };
    const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
    client.setQueryData(['account'], account);
    const root = createRoot(dom.window.document.getElementById('root')!);
    async function settle() { await act(async () => { await new Promise(r => setTimeout(r, 30)); }); }
    function button(text: string) { return [...dom.window.document.querySelectorAll('button')].find(b => b.textContent?.toLowerCase().includes(text.toLowerCase()))!; }
    try {
        await act(async () => { root.render(createElement(QueryClientProvider, { client }, createElement(MemoryRouter, null, createElement(OperationsReportsPage)))); });
        await settle();
        await act(async () => button('flooding').click());
        await settle();
        await act(async () => { dom.window.document.querySelector('form')!.dispatchEvent(new dom.window.Event('submit', { bubbles: true, cancelable: true })); });
        await settle();
        assert.equal(button('I reviewed the updated case').disabled, true, 'failed refresh must not unlock review');
        await act(async () => button('flooding').click());
        await settle();
        assert.equal(dom.window.document.querySelector('fieldset')!.disabled, true, 'same row must retain review guard');
        refreshOK = true;
        await act(async () => button('Retry').click());
        await settle();
        assert.equal(button('I reviewed the updated case').disabled, false);
        await act(async () => button('I reviewed the updated case').click());
        await settle();
        assert.equal(dom.window.document.querySelector('fieldset')!.disabled, false);
        await act(async () => { client.setQueryData(['account'], { ...account, id: 'other', capabilities: [] }); });
        await settle();
        assert.equal(dom.window.document.querySelector('form'), null, 'permission/account change hides private form');
        assert.ok(!dom.window.document.body.textContent!.includes('3, 101'), 'private location must clear');
    }
    finally {
        await act(async () => root.unmount());
        client.clear();
        globalThis.fetch = originalFetch;
        dom.window.close();
        for (const n of names) {
            const d = previous.get(n);
            if (d)
                Object.defineProperty(globalThis, n, d);
            else
                Reflect.deleteProperty(globalThis, n);
        }
    }
});

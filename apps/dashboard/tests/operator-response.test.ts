import test from 'node:test';
import assert from 'node:assert/strict';
import { responseActions, responseEventBody } from '../src/api/operator-response';
import { ordinaryCapabilities } from '../src/api/admin';
test('response actions preserve closure and revision guards', () => {
    assert.deepEqual(responseActions('closed'), ['reopen']);
    assert.ok(responseActions('unassigned').includes('inspect'));
    assert.ok(!responseActions('investigating').includes('reopen'));
    assert.ok((ordinaryCapabilities as readonly string[]).includes('report:respond'));
    assert.deepEqual(responseEventBody(3, 'act', 'Checked site', { note: 'Cleared inlet debris' }), { expected_revision: 3, action: 'act', reason: 'Checked site', note: 'Cleared inlet debris' });
});

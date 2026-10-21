import test from 'node:test'
import assert from 'node:assert/strict'
import { observationSummary } from '../src/api/observations'
test('unknown, trace and numeric zero remain distinct',()=>{
 assert.match(observationSummary({kind:'rain_occurrence',response:'unknown'}),/Unknown/)
 assert.match(observationSummary({kind:'rainfall_accumulation',amount_state:'trace',unit:'mm'}),/Trace/)
 assert.match(observationSummary({kind:'rainfall_accumulation',amount_state:'value',value:0,unit:'mm'}),/0 mm/)
 assert.match(observationSummary({kind:'water_reading',value:-.2,unit:'m',reference_kind:'stage',reference_id:'ref',reference_revision:1}),/stage/)
})
test('movement is rendered as observation context',()=>{
 assert.match(observationSummary({kind:'flooding',response:'present',movement:'flowing'}),/Movement: flowing/)
})

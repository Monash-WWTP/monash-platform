import test from 'node:test'
import assert from 'node:assert/strict'
import { JSDOM } from 'jsdom'
import { revealInvalidField } from '../src/components/scenario/validationFocus'

test('invalid fields inside closed disclosures are revealed, described and focused', () => {
 const { document } = new JSDOM('<main><details><summary>Carbon accounting</summary><input aria-label="Recovered CH₄ (kg/m³)"></details><p id="scenario-error">Recovery must be non-negative</p></main>').window
 const root = document.querySelector('main')!
 revealInvalidField(root, 'Recovered CH₄ (kg/m³)')
 const input = root.querySelector('input')!
 assert.equal(root.querySelector('details')!.open, true)
 assert.equal(document.activeElement, input)
 assert.equal(input.getAttribute('aria-invalid'), 'true')
 assert.equal(input.getAttribute('aria-describedby'), 'scenario-error')
})

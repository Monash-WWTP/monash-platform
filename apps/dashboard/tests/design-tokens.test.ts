import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import assert from 'node:assert/strict'

const indexCss = readFileSync(new URL('../src/index.css', import.meta.url), 'utf8')
const publicCss = readFileSync(new URL('../src/pages/public/public.css', import.meta.url), 'utf8')
const chartPalette = readFileSync(new URL('../src/components/dashboard/chartPalette.ts', import.meta.url), 'utf8')
const uiComponents = readFileSync(new URL('../src/components/ui.tsx', import.meta.url), 'utf8')
const mapPage = readFileSync(new URL('../src/pages/MapPage.tsx', import.meta.url), 'utf8')
const resultsPanel = readFileSync(new URL('../src/components/results/ResultsPanel.tsx', import.meta.url), 'utf8')
const comparisonView = readFileSync(new URL('../src/components/comparison/ComparisonView.tsx', import.meta.url), 'utf8')

test('canonical browser tokens use the approved landing page palette and type', () => {
  for (const [name, value] of Object.entries({
    ink: '#202724',
    muted: '#58635d',
    rule: '#dbe2dd',
    green: '#146346',
    'green-hover': '#0c4d35',
    soft: '#f2f6f3',
  })) {
    assert.match(indexCss, new RegExp(`--brand-${name}:\\s*${value.replace('#', '\\#')}`, 'i'))
  }

  assert.match(indexCss, /font-family:\s*Manrope,\s*sans-serif/i)
  assert.match(indexCss, /--primary:\s*var\(--brand-green\)/)
  assert.match(indexCss, /--foreground:\s*var\(--brand-ink\)/)
  assert.match(publicCss, /--green:\s*var\(--brand-green\)/)
  assert.match(publicCss, /--ink:\s*var\(--brand-ink\)/)
  assert.match(chartPalette, /series:\s*'#146346'/)
  assert.match(chartPalette, /axis:\s*'#58635d'/)
  assert.match(chartPalette, /grid:\s*'#dbe2dd'/)
})

test('dashboard statuses use shared warning and success roles', () => {
  assert.match(indexCss, /--status-warning:\s*#805314/i)
  assert.match(indexCss, /--color-warning:\s*var\(--status-warning\)/)
  assert.match(uiComponents, /low:\s*'text-success bg-success-soft border-success\/30'/)
  assert.match(uiComponents, /medium:\s*'text-warning bg-warning-soft border-warning\/30'/)
  for (const surface of [mapPage, resultsPanel, comparisonView]) {
    assert.doesNotMatch(surface, /text-amber|bg-amber|border-amber/)
    assert.match(surface, /text-warning|border-warning/)
  }
})

// Inject explicitly through preview_evaluate on the local test page before SPA navigation.
// API calls are synthetic. Reset with a full navigation; never use against production.
(() => {
  const original = window.fetch.bind(window)
  const plant = { id: 1, code: 'QA001', name: 'Synthetic review station', latitude: 3.1012,
    longitude: 101.6394, capacity_mld: 10, status: 'unknown', description: 'Synthetic browser fixture' }
  const sample = { id: 1, station_code: 'QA001', sample_date: '2025-01-01', sampling: 1,
    sample_point: 'Final effluent', bod: 2, bod_bdl: true, cod: null, cod_bdl: false,
    nh3n: null, nh3n_bdl: false, no3n: null, no3n_bdl: false, ph: null, ph_bdl: false,
    oil_grease: null, oil_grease_bdl: false, tss: null, tss_bdl: false,
    temperature: null, compliance: '', source_year: 2025 }
  window.monashFixture = { mode: 'bdl', plantsUnavailable: false }
  window.fetch = async (input, init) => {
    const url = new URL(typeof input === 'string' ? input : input.url, location.href)
    if (!url.pathname.startsWith('/api/')) return original(input, init)
    let body = [], status = 200
    const page = items => ({ items, total: items.length, offset: 0, limit: 500 })
    if (url.pathname === '/api/v1/plants') {
      if (window.monashFixture.plantsUnavailable) { status = 503; body = { error: { message: 'Synthetic outage' } } }
      else body = [plant]
    } else if (url.pathname === '/api/v1/plants/1') body = { ...plant, units: [], compliance_limits: [] }
    else if (url.pathname.endsWith('/stations')) body = page([{ ...plant, stp_type: 'synthetic', category: 'B' }])
    else if (url.pathname.endsWith('/years')) body = [2025]
    else if (url.pathname.endsWith('/samples')) {
      if (window.monashFixture.mode === 'error') { status = 503; body = { error: { message: 'Synthetic outage' } } }
      else body = page(window.monashFixture.mode === 'empty' ? [] : window.monashFixture.mode === 'mixed'
        ? [sample, { ...sample, id: 2, bod: 2, bod_bdl: false }, { ...sample, id: 3, bod: 4, bod_bdl: false }] : [sample])
    } else if (url.pathname.endsWith('/observations')) body = page([])
    else if (url.pathname.endsWith('/me')) { status = 401; body = { error: { message: 'Sign in required' } } }
    return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
  }
  return 'Synthetic monitoring fixture installed'
})()

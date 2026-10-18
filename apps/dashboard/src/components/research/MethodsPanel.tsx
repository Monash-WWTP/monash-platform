/** Scientific status is independent of successful software execution. */
export default function MethodsPanel() {
  return <details className="rounded border border-border bg-card p-3 text-sm">
    <summary className="min-h-6 cursor-pointer font-medium">Methods and sources · unvalidated research</summary>
    <div className="mt-3 max-w-4xl space-y-3 text-xs leading-relaxed text-muted-foreground">
      <p><strong className="text-foreground">Effluent simulation:</strong> effluent_v1 is a deterministic heuristic, not a calibrated ASM1 or plant mass-balance model. Its empirical coefficients lack equation-level study provenance and site validation. No quantified uncertainty is supplied. Decision use is not permitted.</p>
      <p><strong className="text-foreground">GHG accounting:</strong> influent BOD₅/TKN, emission factors and recovered gas feed the guideline’s revised Equations 5.25 and 5.28. GWP values are 28 for CH₄ and 265 for N₂O under that convention. Fixed factors cannot quantify aeration or maintenance intervention benefits. This is not a complete emissions inventory.</p>
      <p>The guideline supports generic integrated aerobic factors, not site accuracy. Methane factors labelled ANAMMOX and AGS are unsupported by the cited methane table. The printed methane recovery-unit placement and nitrogen terminology need clarification. Recovery is subtracted without a zero clamp; evidenced inputs and review are required.</p>
      <p><strong className="text-foreground">Inputs:</strong> defaults are assumptions, not monitoring measurements. TKN means influent Kjeldahl nitrogen; ammonia and final-effluent data are not substitutes. Weather/rainfall are stored as context only. Screening thresholds are not plant permits. Calibration, independent validation and uncertainty assessment remain open.</p>
      <ul className="list-disc space-y-2 pl-5">
        <li><a className="text-primary underline" href="https://doi.org/10.2166/9781789064223" target="_blank" rel="noreferrer">CUWA/IWA carbon-accounting guideline (2024)</a> · revised Eq. 5.25/5.28; Tables 5.6/5.8. <a className="text-primary underline" href="/references/urban-water-carbon-accounting-guidelines.pdf" target="_blank" rel="noreferrer">Read supplied edition</a>.</li>
        <li><a className="text-primary underline" href="https://iwa-mia.org/benchmarking/" target="_blank" rel="noreferrer">IWA benchmarking framework</a> · verification methods; does not validate this heuristic.</li>
        <li><a className="text-primary underline" href="https://doi.org/10.2166/wst.2023.420" target="_blank" rel="noreferrer">Full-scale N₂O monitoring study (2023)</a> · supports the need to assess variation, not fixed-factor causal predictions.</li>
      </ul>
      <p>Source audit: 18 October 2026. Passing software tests does not establish scientific validity.</p>
    </div>
  </details>
}

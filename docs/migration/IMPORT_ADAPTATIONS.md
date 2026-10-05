# Import adaptations

The dashboard source was copied from `wwtp-dashboard` commit `202b72e`.
`npm ci` and `npm run build` passed on the pinned snapshot. Its `npm run lint`
reported six inherited errors: five `react-refresh/only-export-components`
and one `react-hooks/use-memo`. The initial successor import made these changes:

| Source path prefix `frontend/` | Adaptation |
| --- | --- |
| `src/components/dashboard/TrendsChart.tsx` | Move shared `CHART` constant to `chartPalette.ts` so the component file exports only a component. |
| `src/components/comparison/ComparisonView.tsx` | Import `CHART` from the palette module. |
| `src/components/monitoring/StationDashboard.tsx` | Import `CHART` from the palette module. |
| `src/components/twin/DigitalTwin.tsx` | Pass an inline callback to `useMemo`, as required by the React hook lint rule. |
| `src/components/ui.tsx` | Stop exporting the locally used `severityColor` constant. |
| `src/components/ui/badge.tsx` | Stop exporting an unused variant builder. |
| `src/components/ui/button.tsx` | Stop exporting an unused variant builder. |
| `src/components/ui/tabs.tsx` | Stop exporting an unused variant builder. |

The source inventory retains each original blob hash. The import test requires
every other dashboard file to remain byte-identical. These adaptations do not
change data endpoints or chart values; lint and production build pass after
the changes. The dependency audit reported 22 advisories on the inherited
lockfile and requires a separate dependency review rather than an automatic
major-version update during source import.

## CitizenFlood

The mobile app was copied from `citizenflood` commit `5a80700`. Its committed
`pubspec.lock` is byte-identical; the two uncommitted changes in the legacy
checkout were not copied or modified. The successor copy changes only
`android/gradle.properties`: Gradle's inherited 8 GB heap and 4 GB metaspace
caused a local OOM kill before it produced an APK. The successor limits the
heap to 2 GB, metaspace to 1 GB, and Gradle workers to two. The import test
requires all other imported mobile files to match their source blobs.

## Documentation and research relocation

Active app READMEs now describe successor paths and current integrations; original READMEs remain under `docs/legacy/*/APP_README.md`. The public data dictionary has relocated license/helper/attribution links. The notebook reads the pinned local snapshot instead of a moving remote main branch and has cleared stored outputs. Its scientific summaries are unchanged. The Python lock now includes an optional research plotting group.

Three raw CSVs were reclassified as restricted after checking the license scope. The unsupported final-effluent GHG helper and unrestricted live exporter were reclassified as inactive legacy references. No public CSV values or original snapshot manifest were changed.

## Dashboard dependency remediation

The imported audit failed with 17 runtime advisory entries (one critical). Removed the unused `deck.gl` umbrella package; the actual imports use `@deck.gl/react` and `@deck.gl/layers`. Upgraded MapLibre from 5.24.0 to 6.11.2 and changed `MapPage.tsx` to its namespace import because v6 has no default export. Compatible `npm audit fix` updates resolve the remaining packages. Both `package.json` and lockfile are explicit import adaptations. The audit, TypeScript build and lint pass after these changes; CI now rejects high/critical runtime advisories.

The relevant MapLibre sanitizer fix is described in the [official advisory](https://github.com/maplibre/maplibre-gl-js/security/advisories/GHSA-jrc7-96c5-q579). Browser release QA remains required for live integrations.

MapLibre v6 also needs a bundled worker. The synthetic browser check exposed missing worker loading; `MapPage.tsx` now imports `maplibre-gl-worker.mjs?worker&url` and calls `setWorkerUrl`, following the [official Vite installation guidance](https://maplibre.org/maplibre-gl-js/docs/). The production browser smoke verifies this worker and sanitizer behavior with no live application data.

Final review found the inherited mobile launcher had Git mode 100644 although its README calls it directly. The successor commits mode 100755; script bytes remain identical. An executable-permission regression check fails on the inherited mode and passes after correction.

## Public portal route adaptations

The successor now owns public routes at `/`; `src/main.tsx` uses lazy operator route loading under `/dashboard`. `src/pages/MapPage.tsx` and `src/pages/WorkspacePage.tsx` update plant and back-to-map navigation. Legacy plant paths redirect through a new component. The import regression allowlist explicitly records these files; original source hashes and inactive legacy references are retained. `package.json` and its lock add tsx for metadata validation tests. New public routes do not change monitoring endpoints or simulation values.

## Vercel successor deployment

`apps/dashboard/vercel.json` now specifies the Vite build/output and an SPA fallback after the inherited legacy `/api` proxy. The existing Render target is retained during client cutover. Root deployment settings use `apps/dashboard`; `.vercelignore` restricts uploads to the frontend and excludes local secrets/dependencies/build output. Vercel project state and local OIDC credentials are ignored. This deployment does not establish shared identity or successor API integration.

## Cross-platform consistency follow-up

The 2026-10-05 visual alignment updates the imported dashboard's `src/index.css` and `src/components/scenario/ScenarioPanel.tsx`, and the imported mobile model, theme, category tile, report/map screens and category-tile test. Their new hashes are intentionally different from the pinned source snapshot; `tests/test_client_imports.py` records these exact paths as adaptations. Browser styles consume the landing page's canonical semantic colors and Manrope; Android mirrors its green/neutral palette with Material components, replaces category emoji with named icons and avoids duplicate screen-reader category labels. These UI changes do not alter backend contracts or the already published Android artifact.

The follow-up status-color audit also updates dashboard severity badges and warnings to use shared semantic roles. It does not change status meaning or model results.

The supplied guideline's first page is rendered as a static cover image on the research references page only. The landing page links to general research without exposing this specific publication. Visitors open or download the original PDF from the reference entry; the site does not embed a scrollable PDF viewer.

# Import adaptations

The dashboard source was copied from `wwtp-dashboard` commit `202b72e`.
`npm ci` and `npm run build` passed on the pinned snapshot. Its `npm run lint`
reported six inherited errors: five `react-refresh/only-export-components`
and one `react-hooks/use-memo`. The successor copy makes only these changes:

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

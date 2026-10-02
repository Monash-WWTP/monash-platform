# Source origins and import policy

| Source | Pinned revision | Intended destination |
| --- | --- | --- |
| `Monash-WWTP/citizenflood` | `5a80700` | `apps/citizenflood`; historical Supabase material under `legacy/` |
| `Monash-WWTP/wwtp-dashboard` | `202b72e` | `apps/dashboard`, research, public data, historical documentation |
| Local `monash-platform-api` | `d518a95` | `services/api`, `packages/simulation`, root uv workspace |

The machine-readable [inventory](source-inventory.json) records every tracked
file at these revisions, its SHA-256 hash, and its import disposition. The
successor starts a new Git history; the legacy repositories retain their full
history and deployed role. No production endpoint changes during import.

The old `citizenflood` checkout has unrelated uncommitted edits to
`analysis_options.yaml` and `pubspec.lock`. This import uses committed blob
bytes only and leaves those edits in place for a separate review. The project
spreadsheet is held from import pending rights and personal-data review.

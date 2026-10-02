# Source origins and import record

Imported on 2026-10-02 into a new local Git history. Legacy repositories retain their history and deployed role.

| Source | Exact revision | Destination |
| --- | --- | --- |
| [Monash-WWTP/citizenflood](https://github.com/Monash-WWTP/citizenflood) | `5a80700671a85089ba284e3ea47dfa0b1ddcbdc5` | `apps/citizenflood`, inactive Supabase/docs references |
| [Monash-WWTP/wwtp-dashboard](https://github.com/Monash-WWTP/wwtp-dashboard) | `202b72e9bd6394acae37dec8d5556ff555572f41` | `apps/dashboard`, public snapshot, research and historical references |
| Local monash-platform-api foundation | `d518a95b2cb46f8b9faee9ab3363050a5528d566` | `services/api`, `packages/simulation`, root uv workspace |

The [machine-readable inventory](source-inventory.json) accounts for all 207 tracked source files with original SHA-256, source path, destination or reason. Dispositions after rights/science review: 1 generated, 142 imported, 27 legacy_reference, 4 restricted, 33 superseded.

The old dashboard backend/simulation is superseded by the pinned extracted API foundation. Root ignore/CI files are replaced by successor policies. Flutter `.metadata` is regenerated. No application code is silently omitted. Path/lint/toolchain/documentation adaptations are in [IMPORT_ADAPTATIONS.md](IMPORT_ADAPTATIONS.md). Original app READMEs and other inactive material are kept for provenance.

The two pre-existing CitizenFlood edits in `analysis_options.yaml` and `pubspec.lock` remain in the legacy checkout; only committed source blobs were imported. Both legacy checkouts must retain their original status throughout implementation.

## Restricted material and retrieval

The project spreadsheet `Monash Flutter App Dev.xlsx` is withheld pending rights/personal-data review. The raw `data-to-upload/2023.csv`, `2024.csv`, and `2025.csv` are outside the explicit public-data license and are withheld pending rights review. Their source revisions and SHA-256 values remain in the inventory. No permission is inferred from the public snapshot's license.

An authorized custodian can retrieve each exact blob from the existing controlled checkout with `git show <source_commit>:<source_path>` into approved private storage, then compare SHA-256 with the inventory. Do not place the material in this repo until rights/privacy review and a recorded disposition update. Public station coordinates are already in the licensed snapshot; the historical duplicate is retained in research.

## Verification

CI can run `python scripts/check_import_inventory.py --verify-targets` without source checkouts. This verifies recorded dispositions and destinations. A full origin audit additionally supplies all three `--source NAME=PATH` arguments; it compares every pinned Git-tree path/hash. Source parity tests enforce unchanged client files with explicitly listed adaptations. The public CSVs/manifest and all mapped inactive references retain their original bytes. New research outputs are not fabricated as imported source.

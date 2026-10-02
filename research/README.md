# Reproducible exploratory analysis

The adapted notebook reads only the pinned `data/public` snapshot. It summarizes source-recorded status and non-BDL BOD/COD values. It computes no GHG inventory and no independent legal compliance assessment.

From the repo root:

```sh
uv sync --locked --group research
uv run --locked --group research python research/run_notebook.py
uv run --locked pytest -q tests/test_public_data.py
```

The runner executes every committed code cell with a noninteractive plotting backend. The research dependency group is locked separately from the default API environment. Run the notebook from the root or notebook directory in an editor if desired.

Raw 2023–2025 source CSVs are held outside this repo pending rights review; their hashes and source paths are in the import inventory. The old GHG helper and live Supabase export are preserved under `legacy/`, outside this reproduction path. `data-preparation/station_locations.json` is a duplicate of the publicly released station coordinates, retained for origin completeness. No approved raw-data ETL is claimed.

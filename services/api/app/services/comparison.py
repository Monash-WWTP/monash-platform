"""Compatibility checks for like-for-like research comparisons, not model validation."""
from datetime import date
import math
import re

from ..db.models import SimulationRun
from ..http.errors import ApiError


def validate_comparison(runs: list[SimulationRun]) -> None:
    def reject(message: str) -> None:
        raise ApiError(422, 'incompatible_runs', message)

    if len({run.id for run in runs}) != len(runs):
        reject('Choose distinct runs for comparison.')
    if any(run.status != 'completed' for run in runs):
        reject('Only completed runs can be compared.')
    identities = {(run.scenario.plant_id, run.model_id, run.model_version, run.artifact_digest) for run in runs}
    if len(identities) != 1 or any(not re.fullmatch(r'sha256:[0-9a-f]{64}', run.artifact_digest or '') for run in runs):
        reject('Runs must belong to the same plant and use the same model version and artifact.')

    for run in runs:
        result = run.timeseries
        if (not isinstance(result, dict)
                or not isinstance(result.get('dates'), list)
                or not isinstance(result.get('series'), dict)):
            reject('Runs need dated result objects with named metric series.')
    reference = runs[0].timeseries
    dates = reference.get('dates', [])
    metrics = set(reference.get('series', {}))
    if not dates or not metrics:
        reject('Runs need dated results before they can be compared.')
    for run in runs:
        ts = run.timeseries or {}
        run_dates = ts.get('dates', [])
        try:
            valid_dates = all(date.fromisoformat(d).isoformat() == d for d in run_dates)
            ordered_dates = sorted(set(run_dates)) == run_dates
        except (TypeError, ValueError):
            valid_dates = ordered_dates = False
        if not valid_dates or not ordered_dates or run_dates != dates:
            reject('Runs must cover exactly the same ordered observation dates.')
        series = ts.get('series', {})
        if set(series) != metrics:
            reject('Runs must contain the same model metrics and units.')
        if any(not isinstance(values, list) or len(values) != len(dates)
               or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values)
               for values in series.values()):
            reject('Every result series must contain one finite value per date.')

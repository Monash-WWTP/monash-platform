"""Parquet persistence for simulation result time-series."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .domain import SimulationResult


def result_to_frame(result: SimulationResult) -> pd.DataFrame:
    data: dict = {"date": [d.isoformat() for d in result.dates]}
    for metric, values in result.predicted_effluent.items():
        data[metric] = values
    data["influent_flow"] = result.influent_flow
    data["capacity_utilization"] = result.capacity_utilization
    for unit, values in result.unit_availability.items():
        data[f"availability_{unit}"] = values
    for gas, values in result.ghg.items():
        data[f"ghg_{gas}"] = values
    return pd.DataFrame(data)


def write_result(result: SimulationResult, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    result_to_frame(result).to_parquet(path, index=False)
    return path


def read_result(path: str | Path) -> pd.DataFrame:
    return pd.read_parquet(path)

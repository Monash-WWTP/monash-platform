"""SimulationModel abstract interface and model registry.

The frontend/API only ever reference models by ``model_id``; swapping or
adding models means registering another implementation here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .domain import SimulationInput, SimulationResult


class SimulationModel(ABC):
    model_id: str = ""
    name: str = ""
    version: str = ""
    description: str = ""

    @abstractmethod
    def run(self, sim_input: SimulationInput) -> SimulationResult:
        """Run the simulation and return predicted effluent, KPIs and risks."""


MODEL_REGISTRY: dict[str, SimulationModel] = {}


def register_model(model: SimulationModel) -> None:
    MODEL_REGISTRY[model.model_id] = model


def get_model(model_id: str) -> SimulationModel:
    if model_id not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model_id: {model_id!r}")
    return MODEL_REGISTRY[model_id]


def list_models() -> list[dict[str, str]]:
    return [
        {
            "model_id": m.model_id,
            "name": m.name,
            "version": m.version,
            "description": m.description,
        }
        for m in MODEL_REGISTRY.values()
    ]

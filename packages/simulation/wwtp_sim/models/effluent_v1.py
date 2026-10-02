"""Effluent Quality Model v1.

Deterministic daily-timestep process heuristic:

- influent generated from baseline conditions and modulated by demand level.
  Weather and rainfall inputs are retained as scenario context but are not
  applied without a site-specific hydrologic response model.
- per-metric removal efficiencies scaled by equipment availability
  (aeration -> ammonia/BOD/nitrification, clarifier -> TSS/turbidity/P,
  pumps -> hydraulic capacity; overload penalises everything).
- maintenance windows reduce unit availability for their duration.
- GHG scenario estimates (CH4, N2O) computed from assumed influent BOD5 and TKN
  using Eq. 5.25 / 5.28 with process-specific emission factors
  (GWP_CH4 = 28, GWP_N2O = 265; IPCC AR5, 100-yr).
"""
from __future__ import annotations

import math
from datetime import timedelta

import numpy as np

from ..carbon_accounting import ch4_intensity_kgco2e_m3, n2o_intensity_kgco2e_m3
from ..domain import (
    EFFLUENT_METRICS,
    HORIZON_DAYS,
    Exceedance,
    SimulationInput,
    SimulationResult,
)
from ..interface import SimulationModel, register_model

DEMAND_MULTIPLIER = {"low": 0.85, "normal": 1.0, "high": 1.25}

DEFAULT_LIMITS = {
    # Fallback screening values only; a plant's configured limits take priority.
    "bod": 50.0,
    "cod": 200.0,
    "tss": 100.0,
}

class EffluentQualityModelV1(SimulationModel):
    model_id = "effluent_v1"
    name = "Effluent Quality Model v1"
    version = "1.4.0"
    description = (
        "Deterministic heuristic scenario model with stateful carbon and "
        "nitrogen surrogates, demand-modulated influent, and bounded "
        "maintenance impacts; not a calibrated ASM1 implementation."
    )

    def run(self, sim_input: SimulationInput) -> SimulationResult:
        n_days = HORIZON_DAYS[sim_input.horizon]
        fc = sim_input.forecast
        op = sim_input.operating_parameters
        dates = [sim_input.start_date + timedelta(days=i) for i in range(n_days)]

        if fc.demand_change_pct is not None:
            demand_mult = max(0.0, 1.0 + fc.demand_change_pct / 100.0)
        else:
            demand_mult = fc.demand_multiplier or DEMAND_MULTIPLIER[fc.demand]

        # --- daily unit availability (baseline minus maintenance windows) ---
        base_avail = {
            "aeration": float(np.clip(op.aeration_availability, 0.0, 100.0)),
            "pump": float(np.clip(op.pump_availability, 0.0, 100.0)),
            "clarifier": float(np.clip(op.clarifier_availability, 0.0, 100.0)),
        }
        avail = {u: np.full(n_days, v) for u, v in base_avail.items()}
        for ev in sim_input.maintenance:
            for i, d in enumerate(dates):
                if ev.active_on(d):
                    avail[ev.unit_type][i] = min(avail[ev.unit_type][i], ev.availability_pct)

        # --- influent series ---
        weekly = 1.0 + 0.06 * np.sin(np.arange(n_days) * 2 * math.pi / 7)
        flow = fc.influent.flow * demand_mult * weekly
        conc_mult = np.full(n_days, demand_mult ** 0.5)
        influent = {
            "bod": fc.influent.bod * conc_mult,
            "cod": fc.influent.cod * conc_mult,
            "tss": fc.influent.tss * conc_mult,
            "ammonia": fc.influent.ammonia * conc_mult,
            "organic_n": np.maximum(
                fc.influent.tkn - fc.influent.ammonia, 0.0
            )
            * conc_mult,
        }

        # --- hydraulic capacity / overload ---
        hydraulic_capacity = op.capacity_mld * avail["pump"] / 100.0
        utilization = flow / np.maximum(hydraulic_capacity, 1e-6)
        overload = np.clip(utilization - 1.0, 0.0, 1.0)  # fraction beyond capacity

        # --- heuristic concentration-surrogate updates ---
        # These are not physical reactor states or a CSTR mass balance. Plant
        # MLD capacity is not reactor volume or hydraulic retention time.
        # Four bounded substeps preserve the existing daily output shape.
        states = {
            "bod": float(max(fc.influent.bod, 0.0)),
            "cod": float(max(fc.influent.cod, 0.0)),
            "tss": float(max(fc.influent.tss, 0.0)),
            "ammonia": float(max(fc.influent.ammonia, 0.0)),
            "organic_n": float(
                max(fc.influent.tkn - fc.influent.ammonia, 0.0)
            ),
            "nitrate": 0.0,
            "nitrification_activity": 1.0,
        }
        effluent = {
            metric: np.zeros(n_days)
            for metric in ("bod", "cod", "tss", "ammonia", "nitrate")
        }
        substep_days = 0.25

        for i in range(n_days):
            aeration = avail["aeration"][i] / 100.0
            clarifier = avail["clarifier"][i] / 100.0
            hydraulic_ratio = flow[i] / max(op.capacity_mld * avail["pump"][i] / 100.0, 1e-6)
            hydraulic_ratio = max(float(hydraulic_ratio), 0.0)
            overload_factor = 1.0 / (1.0 + max(hydraulic_ratio - 1.0, 0.0))
            exchange_factor = min(hydraulic_ratio, 4.0)

            for _ in range(4):
                states["nitrification_activity"] += substep_days * 0.45 * (
                    aeration - states["nitrification_activity"]
                )
                for metric in ("bod", "cod", "tss", "ammonia", "organic_n"):
                    incoming_concentration = influent[metric][i]
                    states[metric] += substep_days * exchange_factor * (
                        incoming_concentration - states[metric]
                    )
                states["nitrate"] += substep_days * exchange_factor * (
                    -states["nitrate"]
                )

                # Heterotrophic carbon oxidation and autotrophic nitrification.
                carbon_rate = (7.0 * aeration + 0.2) * overload_factor
                states["bod"] *= math.exp(-substep_days * carbon_rate)
                states["cod"] *= math.exp(
                    -substep_days * (4.0 * aeration + 0.2) * overload_factor
                )
                mineralized = states["organic_n"] * (
                    1.0 - math.exp(-substep_days * 0.3 * overload_factor)
                )
                states["organic_n"] -= mineralized
                states["ammonia"] += mineralized
                nitrified = states["ammonia"] * (
                    1.0
                    - math.exp(
                        -substep_days
                        * 2.5
                        * states["nitrification_activity"]
                        * overload_factor
                    )
                )
                states["ammonia"] -= nitrified
                states["nitrate"] += nitrified * 0.85

                # Denitrification consumes a bounded share of available carbon.
                denit = min(
                    states["nitrate"],
                    substep_days
                    * (0.8 * (1.0 - 0.4 * aeration))
                    * overload_factor
                    * states["nitrate"]
                    * min(states["bod"] / max(influent["bod"][i], 1.0), 1.0),
                )
                states["nitrate"] -= denit
                states["bod"] = max(states["bod"] - denit * 0.25, 0.0)
                for metric, value in states.items():
                    states[metric] = max(value, 0.0)
                states["nitrification_activity"] = min(
                    states["nitrification_activity"], 1.0
                )

            effluent["bod"][i] = states["bod"]
            effluent["cod"][i] = states["cod"]
            effluent["ammonia"][i] = states["ammonia"]
            effluent["nitrate"][i] = states["nitrate"]
            effluent["tss"][i] = states["tss"] * (1.0 - 0.95 * clarifier)

        # --- derived metrics ---
        effluent["phosphorus"] = np.clip(
            4.5 * (1.0 - 0.75 * avail["clarifier"] / 100.0) + 0.8 + 1.5 * overload, 0.3, None
        )
        effluent["turbidity"] = np.clip(effluent["tss"] * 0.55 + 1.0, 0.5, None)
        effluent["ph"] = 7.2 - 0.15 * (1.0 - avail["aeration"] / 100.0) * 2.0

        limits = {**DEFAULT_LIMITS, **sim_input.compliance_limits}

        # --- KPIs ---
        violations = np.zeros(n_days, dtype=bool)
        per_metric_compliance: dict[str, float] = {}
        for metric, limit in limits.items():
            if metric == "ph":
                continue
            exceed = effluent[metric] > limit
            violations |= exceed
            per_metric_compliance[metric] = float(100.0 * (1.0 - exceed.mean()))
        compliance_pct = float(100.0 * (1.0 - violations.mean()))
        avg_utilization = float(np.clip(utilization, 0, 2).mean() * 100.0)

        # --- GHG emission intensities (Guideline Eq. 5.25 / 5.28) ---
        # Equation 5.28 requires influent Kjeldahl nitrogen (TKN), not ammonia.
        # The backend supplies a documented baseline TKN for older payloads.
        ef = sim_input.emission_factors
        influent_tkn = fc.influent.tkn * conc_mult
        ghg_ch4 = ch4_intensity_kgco2e_m3(
            influent["bod"],
            ef.ef_ch4,
            op.ch4_recovered_kg_m3,
        )
        ghg_n2o = n2o_intensity_kgco2e_m3(
            influent_tkn,
            ef.ef_n2o,
            op.n2o_recovered_kg_m3,
        )
        ghg_total = ghg_ch4 + ghg_n2o
        # MLD x 1,000 = m3/day. This converts intensity into an operational
        # daily footprint and supports a horizon total.
        ghg_total_kgco2e_day = ghg_total * flow * 1_000.0

        kpis: dict[str, float | str] = {
            "compliance_pct": round(compliance_pct, 1),
            "exceedance_days": int(violations.sum()),
            "capacity_utilization_pct": round(avg_utilization, 1),
            "ch4_mean_kgco2e_m3": round(float(ghg_ch4.mean()), 4),
            "n2o_mean_kgco2e_m3": round(float(ghg_n2o.mean()), 4),
            "ghg_mean_kgco2e_m3": round(float(ghg_total.mean()), 4),
            "ghg_mean_kgco2e_day": round(float(ghg_total_kgco2e_day.mean()), 2),
            "ghg_total_kgco2e": round(float(ghg_total_kgco2e_day.sum()), 2),
            **{f"compliance_{m}": round(v, 1) for m, v in per_metric_compliance.items()},
        }

        exceedances = self._detect_exceedances(effluent, limits, avail, overload)

        return SimulationResult(
            dates=dates,
            predicted_effluent={m: [round(float(v), 3) for v in effluent[m]] for m in EFFLUENT_METRICS},
            influent_flow=[round(float(v), 2) for v in flow],
            capacity_utilization=[round(float(v) * 100.0, 1) for v in utilization],
            unit_availability={u: [float(v) for v in a] for u, a in avail.items()},
            ghg={
                "ch4": [round(float(v), 5) for v in ghg_ch4],
                "n2o": [round(float(v), 5) for v in ghg_n2o],
                "total": [round(float(v), 5) for v in ghg_total],
                "total_kgco2e_day": [round(float(v), 2) for v in ghg_total_kgco2e_day],
            },
            kpis=kpis,
            exceedances=exceedances,
            model_id=self.model_id,
            model_version=self.version,
        )

    def _detect_exceedances(self, effluent, limits, avail, overload) -> list[Exceedance]:
        out: list[Exceedance] = []
        for metric, limit in limits.items():
            exceed = np.asarray(effluent[metric]) > limit
            for start, end in _spans(exceed):
                peak = float(np.max(effluent[metric][start:end]))
                factors = [
                    f"reduced {unit} availability"
                    for unit in ("aeration", "clarifier", "pump")
                    if np.any(avail[unit][start:end] < 100.0)
                ]
                if np.any(overload[start:end] > 0):
                    factors.append("flow above hydraulic capacity")
                out.append(
                    Exceedance(
                        metric=metric,
                        start_day=int(start),
                        end_day=int(end - 1),
                        peak_value=round(peak, 2),
                        limit_value=float(limit),
                        peak_ratio=round(peak / limit, 2),
                        factors=factors,
                    )
                )
        out.sort(key=lambda e: (-e.peak_ratio, e.start_day))
        return out[:20]


def _spans(mask: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous True spans as (start, end-exclusive)."""
    spans = []
    start = None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            spans.append((start, i))
            start = None
    if start is not None:
        spans.append((start, len(mask)))
    return spans


register_model(EffluentQualityModelV1())

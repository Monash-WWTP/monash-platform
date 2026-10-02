"""Fixed calculation case to catch changes during package extraction."""

from datetime import date

import pytest

from wwtp_sim import get_model
from wwtp_sim.domain import (
    EmissionFactors,
    Forecast,
    InfluentConditions,
    OperatingParameters,
    SimulationInput,
)


def test_extracted_model_retains_reference_case():
    model = get_model("effluent_v1")
    result = model.run(
        SimulationInput(
            forecast=Forecast(
                influent=InfluentConditions(
                    flow=6, bod=250, cod=520, tss=300, ammonia=30, tkn=40
                )
            ),
            maintenance=[],
            operating_parameters=OperatingParameters(capacity_mld=10),
            horizon="3_months",
            start_date=date(2026, 1, 1),
            emission_factors=EmissionFactors(ef_ch4=0.0121, ef_n2o=0.0093),
        )
    )
    assert result.model_id == "effluent_v1"
    assert result.model_version == "1.4.0"
    assert len(result.dates) == 90
    assert result.ghg["ch4"][0] == pytest.approx(0.0847, rel=1e-3)
    assert result.ghg["n2o"][0] == pytest.approx(0.1549, rel=1e-3)
    assert {"ghg_mean_kgco2e_m3", "compliance_pct"} <= result.kpis.keys()

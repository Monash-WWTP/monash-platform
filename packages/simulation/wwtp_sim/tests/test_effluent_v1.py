from datetime import date

import pytest

from wwtp_sim import (
    EmissionFactors,
    Forecast,
    InfluentConditions,
    MaintenanceEvent,
    OperatingParameters,
    SimulationInput,
    get_model,
    list_models,
)
from wwtp_sim.domain import EFFLUENT_METRICS, HORIZON_DAYS


def make_input(**overrides) -> SimulationInput:
    defaults = dict(
        forecast=Forecast(),
        maintenance=[],
        operating_parameters=OperatingParameters(),
        horizon="3_months",
        start_date=date(2026, 7, 1),
    )
    defaults.update(overrides)
    return SimulationInput(**defaults)


@pytest.fixture
def model():
    return get_model("effluent_v1")


def test_model_registered():
    ids = [m["model_id"] for m in list_models()]
    assert "effluent_v1" in ids


def test_output_shape(model):
    for horizon, days in HORIZON_DAYS.items():
        result = model.run(make_input(horizon=horizon))
        assert len(result.dates) == days
        for metric in EFFLUENT_METRICS:
            assert len(result.predicted_effluent[metric]) == days
        assert len(result.ghg["ch4"]) == days
        assert len(result.ghg["n2o"]) == days
        assert {
            "compliance_pct",
            "exceedance_days",
            "capacity_utilization_pct",
            "ch4_mean_kgco2e_m3",
            "n2o_mean_kgco2e_m3",
            "ghg_mean_kgco2e_m3",
        } <= set(result.kpis)


def test_deterministic(model):
    a = model.run(make_input())
    b = model.run(make_input())
    assert a.predicted_effluent == b.predicted_effluent
    assert a.kpis == b.kpis


def test_maintenance_degrades_quality(model):
    baseline = model.run(make_input())
    maint = [
        MaintenanceEvent(
            unit_type="aeration",
            start_date=date(2026, 7, 15),
            duration_days=14,
            availability_pct=50.0,
        )
    ]
    degraded = model.run(make_input(maintenance=maint))

    # ammonia rises during the maintenance window (days 14..27)
    base_nh3 = baseline.predicted_effluent["ammonia"]
    deg_nh3 = degraded.predicted_effluent["ammonia"]
    window = slice(14, 28)
    assert sum(deg_nh3[window]) > sum(base_nh3[window]) * 1.5
    assert degraded.kpis["compliance_pct"] <= baseline.kpis["compliance_pct"]


def test_maintenance_has_bounded_stateful_recovery(model):
    baseline = model.run(make_input(horizon="3_months"))
    maint = [
        MaintenanceEvent(
            unit_type="aeration",
            start_date=date(2026, 7, 15),
            duration_days=7,
            availability_pct=0.0,
        )
    ]
    degraded = model.run(make_input(maintenance=maint))

    # The process state should remain impaired immediately after maintenance,
    # then recover toward baseline rather than jumping back in one day.
    ammonia = degraded.predicted_effluent["ammonia"]
    base_ammonia = baseline.predicted_effluent["ammonia"]
    assert ammonia[21] > base_ammonia[21]
    assert ammonia[28] > base_ammonia[28]
    assert ammonia[28] < ammonia[21]


def test_stateful_outputs_are_finite_and_nonnegative(model):
    result = model.run(
        make_input(
            forecast=Forecast(weather="wet", demand="high"),
            operating_parameters=OperatingParameters(
                capacity_mld=1.0,
                aeration_availability=0.0,
                pump_availability=0.0,
                clarifier_availability=0.0,
            ),
        )
    )

    for values in result.predicted_effluent.values():
        assert all(value >= 0 for value in values)
        assert all(value < float("inf") for value in values)


def test_tkn_drives_nitrogen_process_load(model):
    low_tkn = model.run(
        make_input(
            forecast=Forecast(
                weather="dry",
                influent=InfluentConditions(ammonia=20.0, tkn=20.0),
            )
        )
    )
    high_tkn = model.run(
        make_input(
            forecast=Forecast(
                weather="dry",
                influent=InfluentConditions(ammonia=20.0, tkn=60.0),
            )
        )
    )

    assert sum(high_tkn.predicted_effluent["nitrate"]) > sum(
        low_tkn.predicted_effluent["nitrate"]
    )
    assert max(high_tkn.predicted_effluent["nitrate"]) <= 60.0 * 1.06


def test_equipment_availability_changes_process_outcomes(model):
    healthy = model.run(make_input())
    impaired = model.run(
        make_input(
            operating_parameters=OperatingParameters(
                capacity_mld=60.0,
                aeration_availability=0.0,
                pump_availability=50.0,
                clarifier_availability=0.0,
            )
        )
    )

    assert sum(impaired.predicted_effluent["ammonia"]) > sum(
        healthy.predicted_effluent["ammonia"]
    )
    assert sum(impaired.predicted_effluent["tss"]) > sum(
        healthy.predicted_effluent["tss"]
    )
    assert impaired.kpis["capacity_utilization_pct"] > healthy.kpis[
        "capacity_utilization_pct"
    ]


def test_unvalidated_weather_inputs_do_not_change_model_outputs(model):
    baseline = model.run(
        make_input(forecast=Forecast(weather="dry", rainfall_mm_day=0.0))
    )
    weather_changed = model.run(
        make_input(forecast=Forecast(weather="wet", rainfall_mm_day=200.0))
    )

    assert weather_changed.influent_flow == baseline.influent_flow
    assert weather_changed.predicted_effluent == baseline.predicted_effluent
    assert weather_changed.ghg == baseline.ghg
    assert weather_changed.kpis == baseline.kpis


def test_numeric_demand_drives_forecast(model):
    baseline = model.run(make_input())
    quantitative = model.run(
        make_input(
            forecast=Forecast(
                demand_change_pct=25.0,
            )
        )
    )

    assert sum(quantitative.influent_flow) > sum(baseline.influent_flow)
    assert quantitative.kpis["capacity_utilization_pct"] > baseline.kpis[
        "capacity_utilization_pct"
    ]


def test_zero_rainfall_preserves_baseline_influent_flow(model):
    result = model.run(
        make_input(
            forecast=Forecast(
                demand_change_pct=0.0,
                rainfall_mm_day=0.0,
            )
        )
    )
    assert result.influent_flow[0] == pytest.approx(40.0)


def test_high_demand_increases_load(model):
    normal = model.run(make_input())
    high = model.run(make_input(forecast=Forecast(demand="high")))
    assert high.kpis["capacity_utilization_pct"] > normal.kpis["capacity_utilization_pct"]


def test_compliance_math(model):
    # absurdly relaxed limits -> 100% compliance, no exceedances
    relaxed = {m: 1e6 for m in ("bod", "cod", "tss", "ammonia", "nitrate", "phosphorus", "turbidity")}
    result = model.run(make_input(compliance_limits=relaxed))
    assert result.kpis["compliance_pct"] == 100.0
    assert result.kpis["exceedance_days"] == 0
    assert result.exceedances == []
    # impossible limits -> 0% compliance, exceedances reported with factual fields
    strict = {m: 1e-6 for m in ("bod", "cod", "tss", "ammonia")}
    result = model.run(make_input(compliance_limits=strict))
    assert result.kpis["compliance_pct"] == 0.0
    assert result.kpis["exceedance_days"] == 90
    assert len(result.exceedances) > 0
    first = result.exceedances[0]
    assert first.peak_value > first.limit_value
    assert first.peak_ratio == pytest.approx(first.peak_value / first.limit_value, rel=0.05)


def test_ghg_equations(model):
    """GHG intensities follow Guideline Eq. 5.25 / 5.28."""
    ef = EmissionFactors(ef_ch4=0.0100, ef_n2o=0.02020)  # SBR
    forecast = Forecast(
        weather="dry",
        influent=InfluentConditions(tkn=50.0),
    )
    result = model.run(make_input(forecast=forecast, emission_factors=ef))
    bod_in = 220.0
    tn_in = 50.0
    expected_ch4 = bod_in * 0.0100 * 28 * 1e-3
    expected_n2o = tn_in * 0.02020 * (44 / 28) * 1e-3 * 265
    assert result.ghg["ch4"][0] == pytest.approx(expected_ch4, rel=1e-3)
    assert result.ghg["n2o"][0] == pytest.approx(expected_n2o, rel=1e-3)
    # process-specific EF changes the result
    general = model.run(make_input(forecast=Forecast(weather="dry")))
    assert general.kpis["n2o_mean_kgco2e_m3"] < result.kpis["n2o_mean_kgco2e_m3"]
    assert result.kpis["ghg_total_kgco2e"] > 0
    assert result.ghg["total"][0] == pytest.approx(expected_ch4 + expected_n2o, rel=1e-3)


def test_ghg_recovery_terms_are_subtracted_as_specified_by_guideline(model):
    forecast = Forecast(
        weather="dry",
        influent=InfluentConditions(tkn=50.0),
    )
    no_recovery = model.run(make_input(forecast=forecast))
    with_recovery = model.run(
        make_input(
            forecast=forecast,
            operating_parameters=OperatingParameters(
                ch4_recovered_kg_m3=0.001,
                n2o_recovered_kg_m3=0.001,
            ),
        )
    )
    assert with_recovery.kpis["ch4_mean_kgco2e_m3"] < no_recovery.kpis["ch4_mean_kgco2e_m3"]
    assert with_recovery.kpis["n2o_mean_kgco2e_m3"] < no_recovery.kpis["n2o_mean_kgco2e_m3"]

    recovered_above_gross = model.run(
        make_input(
            forecast=forecast,
            operating_parameters=OperatingParameters(
                ch4_recovered_kg_m3=1.0,
                n2o_recovered_kg_m3=1.0,
            ),
        )
    )
    expected_ch4 = (220.0 * 0.0121 * 1e-3 - 1.0) * 28
    expected_n2o = (50.0 * 0.0093 * (44 / 28) * 1e-3 - 1.0) * 265
    assert recovered_above_gross.ghg["ch4"][0] == pytest.approx(expected_ch4)
    assert recovered_above_gross.ghg["n2o"][0] == pytest.approx(expected_n2o)
    assert recovered_above_gross.ghg["total"][0] < 0.0


def test_parquet_roundtrip(model, tmp_path):
    from wwtp_sim import read_result, write_result

    result = model.run(make_input(horizon="1_month"))
    path = write_result(result, tmp_path / "run.parquet")
    df = read_result(path)
    assert len(df) == 30
    assert "ammonia" in df.columns and "availability_aeration" in df.columns
    assert "ghg_ch4" in df.columns and "ghg_n2o" in df.columns

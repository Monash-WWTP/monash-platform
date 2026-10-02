"""Run orchestration: scenario row -> wwtp_sim input -> persisted run."""
from __future__ import annotations

from dataclasses import asdict
from datetime import date
import hashlib
import json
from pathlib import Path

from sqlalchemy.orm import Session

from wwtp_sim import (
    EmissionFactors,
    Forecast,
    InfluentConditions,
    MaintenanceEvent,
    OperatingParameters,
    SimulationInput,
    SimulationResult,
    get_model,
)

from ..db.models import Plant, Scenario, SimulationRun


def build_sim_input(scenario: Scenario, plant: Plant) -> SimulationInput:
    fc = scenario.forecast or {}
    influent = fc.get("influent") or {}
    op = scenario.operating_parameters or {}

    maintenance = [
        MaintenanceEvent(
            unit_type=ev["unit_type"],
            start_date=date.fromisoformat(ev["start_date"]),
            duration_days=int(ev["duration_days"]),
            availability_pct=float(ev.get("availability_pct", 50.0)),
        )
        for ev in (scenario.maintenance or [])
    ]

    limits = {cl.metric: cl.limit_value for cl in plant.compliance_limits}

    return SimulationInput(
        forecast=Forecast(
            demand=fc.get("demand", "normal"),
            demand_multiplier=fc.get("demand_multiplier"),
            demand_change_pct=fc.get("demand_change_pct"),
            weather=fc.get("weather", "normal"),
            rainfall_mm_day=fc.get("rainfall_mm_day"),
            influent=InfluentConditions(
                flow=float(influent.get("flow", 40.0)),
                bod=float(influent.get("bod", 220.0)),
                cod=float(influent.get("cod", 480.0)),
                tss=float(influent.get("tss", 240.0)),
                ammonia=float(influent.get("ammonia", 35.0)),
                tkn=float(influent.get("tkn", 40.0)),
            ),
        ),
        maintenance=maintenance,
        operating_parameters=OperatingParameters(
            capacity_mld=float(op.get("capacity_mld") or plant.capacity_mld),
            aeration_availability=float(op.get("aeration_availability", 100.0)),
            pump_availability=float(op.get("pump_availability", 100.0)),
            clarifier_availability=float(op.get("clarifier_availability", 100.0)),
            ch4_recovered_kg_m3=float(op.get("ch4_recovered_kg_m3", 0.0)),
            n2o_recovered_kg_m3=float(op.get("n2o_recovered_kg_m3", 0.0)),
        ),
        horizon=scenario.horizon,
        start_date=date.today(),
        compliance_limits=limits,
        emission_factors=EmissionFactors(ef_ch4=plant.ef_ch4, ef_n2o=plant.ef_n2o),
    )


def result_to_timeseries(result: SimulationResult) -> dict:
    series: dict[str, list[float]] = dict(result.predicted_effluent)
    series["influent_flow"] = result.influent_flow
    series["capacity_utilization"] = result.capacity_utilization
    for unit, values in result.unit_availability.items():
        series[f"availability_{unit}"] = values
    for gas, values in result.ghg.items():
        series[f"ghg_{gas}"] = values
    return {"dates": [d.isoformat() for d in result.dates], "series": series}


def artifact_digest() -> str:
    import wwtp_sim
    roots=[Path(__file__).resolve().parents[1],Path(wwtp_sim.__file__).parent]
    content=b"".join(path.read_bytes() for root in roots for path in sorted(root.rglob("*.py")))
    return "sha256:"+hashlib.sha256(content).hexdigest()


def input_from_snapshot(value: dict) -> SimulationInput:
    forecast={**value["forecast"]}
    forecast["influent"]=InfluentConditions(**forecast["influent"])
    return SimulationInput(forecast=Forecast(**forecast),
        maintenance=[MaintenanceEvent(**{**e,"start_date":date.fromisoformat(e["start_date"])}) for e in value["maintenance"]],
        operating_parameters=OperatingParameters(**value["operating_parameters"]),
        horizon=value["horizon"],start_date=date.fromisoformat(value["start_date"]),
        compliance_limits=value["compliance_limits"],emission_factors=EmissionFactors(**value["emission_factors"]))


def persist_run(db: Session, scenario: Scenario, model_id: str, inputs: SimulationInput,
                parent: SimulationRun | None=None) -> SimulationRun:
    model=get_model(model_id)
    snapshot=json.loads(json.dumps(asdict(inputs),default=lambda v:v.isoformat()))
    plant=scenario.plant
    run=SimulationRun(scenario_id=scenario.id,model_id=model.model_id,model_version=model.version,
        status="running",input_snapshot=snapshot,
        scenario_snapshot=parent.scenario_snapshot if parent else {"id":scenario.id,"name":scenario.name,"horizon":scenario.horizon},
        plant_snapshot=parent.plant_snapshot if parent else {"id":plant.id,"code":plant.code,"name":plant.name,
          "capacity_mld":plant.capacity_mld,"limits":inputs.compliance_limits,"timezone":"UTC"},
        artifact_digest=artifact_digest(),validation_status="illustrative_unvalidated",parent_run_id=parent.id if parent else None,
        kpis={},exceedances=[],timeseries={})
    db.add(run);db.commit();db.refresh(run)
    try:
        result=model.run(inputs)
        run.kpis=result.kpis
        run.exceedances=[asdict(e) for e in result.exceedances]
        run.timeseries=result_to_timeseries(result)
        run.status="completed"
    except Exception:
        run.status="failed";run.error_code="simulation_failed"
    db.commit();db.refresh(run)
    return run


def execute_run(db: Session, scenario: Scenario, model_id: str, start_date: date | None=None) -> SimulationRun:
    inputs=build_sim_input(scenario,scenario.plant)
    if start_date is not None:
        from dataclasses import replace
        inputs=replace(inputs,start_date=start_date)
    return persist_run(db,scenario,model_id,inputs)


def replay_run(db: Session, original: SimulationRun) -> SimulationRun:
    from ..http.errors import ApiError
    if not original.input_snapshot:
        raise ApiError(409,"historical_inputs_unavailable","Historical run inputs were not recorded")
    if get_model(original.model_id).version!=original.model_version:
        raise ApiError(409,"model_version_unavailable","Original model version is unavailable")
    return persist_run(db,original.scenario,original.model_id,input_from_snapshot(original.input_snapshot),original)

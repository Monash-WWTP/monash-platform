from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from wwtp_sim import EFFLUENT_METRICS, list_models
from wwtp_sim.interface import MODEL_REGISTRY

from ..http.errors import ApiError
from ..db.models import Scenario, SimulationRun
from ..db.session import get_db
from ..operator_auth import require_operator
from ..schemas import CompareOut, CompareRequest, ModelOut, RunOut, RunRequest, TimeseriesOut
from ..services.simulation import execute_run, replay_run

router = APIRouter(tags=["simulations"])


def _run_out(run: SimulationRun) -> RunOut:
    return RunOut(
        id=run.id,
        scenario_id=run.scenario_id,
        scenario_name=run.scenario_snapshot.get("name", run.scenario.name),
        plant_id=run.scenario.plant_id,
        horizon=run.scenario_snapshot.get("horizon", run.scenario.horizon),
        model_id=run.model_id,
        model_version=run.model_version,
        status=run.status,
        kpis=run.kpis,
        exceedances=run.exceedances,
        created_at=run.created_at,
        input_snapshot=run.input_snapshot, artifact_digest=run.artifact_digest,
        error_code=run.error_code, parent_run_id=run.parent_run_id,
    )


def _timeseries_out(run: SimulationRun) -> TimeseriesOut:
    ts = run.timeseries or {}
    limits = run.input_snapshot.get("compliance_limits", {})
    return TimeseriesOut(
        run_id=run.id,
        dates=ts.get("dates", []),
        series=ts.get("series", {}),
        compliance_limits=limits,
    )


@router.post("/scenarios/{scenario_id}/run", response_model=RunOut, status_code=201)
def run_scenario(
    scenario_id: int,
    body: RunRequest,
    db: Session = Depends(get_db),
    _operator: str = Depends(require_operator),
):
    scenario = db.get(Scenario, scenario_id)
    if not scenario or scenario.archived:
        raise ApiError(404, "scenario_not_found", "Scenario not found")
    if body.model_id not in MODEL_REGISTRY:
        raise HTTPException(400, f"Unknown model_id: {body.model_id}")
    run = execute_run(db, scenario, body.model_id, body.start_date)
    return _run_out(run)


@router.get("/runs/{run_id}", response_model=RunOut)
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    _operator: str = Depends(require_operator),
):
    run = db.get(SimulationRun, run_id)
    if not run:
        raise ApiError(404, "run_not_found", "Run not found")
    return _run_out(run)


@router.get("/runs/{run_id}/timeseries", response_model=TimeseriesOut)
def get_run_timeseries(
    run_id: int,
    db: Session = Depends(get_db),
    _operator: str = Depends(require_operator),
):
    run = db.get(SimulationRun, run_id)
    if not run:
        raise ApiError(404, "run_not_found", "Run not found")
    return _timeseries_out(run)


@router.post("/compare", response_model=CompareOut)
def compare_runs(
    body: CompareRequest,
    db: Session = Depends(get_db),
    _operator: str = Depends(require_operator),
):
    runs = [db.get(SimulationRun, rid) for rid in body.run_ids]
    missing = [rid for rid, r in zip(body.run_ids, runs) if r is None]
    if missing:
        raise ApiError(404, "run_not_found", "Runs not found", {"run_ids": missing})
    return CompareOut(
        runs=[_run_out(r) for r in runs],
        timeseries=[_timeseries_out(r) for r in runs],
    )


@router.get("/models", response_model=list[ModelOut])
def get_models():
    return list_models()


@router.get("/metrics")
def get_metrics():
    return {"metrics": EFFLUENT_METRICS}


@router.post("/runs/{run_id}/replay",response_model=RunOut,status_code=201)
def replay(run_id:int,db:Session=Depends(get_db),_operator:str=Depends(require_operator)):
    original=db.get(SimulationRun,run_id)
    if not original:raise ApiError(404,"run_not_found","Run not found")
    return _run_out(replay_run(db,original))

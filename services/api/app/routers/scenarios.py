from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..http.errors import ApiError
from ..db.models import Plant, Scenario, SimulationRun
from ..db.session import get_db
from ..operator_auth import require_operator
from ..schemas import ScenarioIn, ScenarioOut

router = APIRouter(tags=["scenarios"])


def _to_out(db: Session, s: Scenario) -> ScenarioOut:
    latest = (
        db.query(SimulationRun.id)
        .filter(SimulationRun.scenario_id == s.id)
        .order_by(SimulationRun.id.desc())
        .first()
    )
    out = ScenarioOut.model_validate(s)
    out.latest_run_id = latest[0] if latest else None
    return out


@router.get("/plants/{plant_id}/scenarios", response_model=list[ScenarioOut])
def list_scenarios(
    plant_id: int,
    db: Session = Depends(get_db),
    _operator: str = Depends(require_operator),
):
    scenarios = db.query(Scenario).filter(Scenario.plant_id == plant_id, Scenario.archived.is_(False)).order_by(Scenario.id).all()
    return [_to_out(db, s) for s in scenarios]


@router.post("/plants/{plant_id}/scenarios", response_model=ScenarioOut, status_code=201)
def create_scenario(
    plant_id: int,
    body: ScenarioIn,
    db: Session = Depends(get_db),
    _operator: str = Depends(require_operator),
):
    if not db.get(Plant, plant_id):
        raise ApiError(404, "plant_not_found", "Plant not found")
    scenario = Scenario(
        plant_id=plant_id,
        name=body.name,
        horizon=body.horizon,
        forecast=body.forecast.model_dump(mode="json"),
        maintenance=[m.model_dump(mode="json") for m in body.maintenance],
        operating_parameters=body.operating_parameters.model_dump(mode="json"),
        is_baseline=body.is_baseline,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return _to_out(db, scenario)


@router.get("/scenarios/{scenario_id}", response_model=ScenarioOut)
def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    _operator: str = Depends(require_operator),
):
    scenario = db.get(Scenario, scenario_id)
    if not scenario or scenario.archived:
        raise ApiError(404, "scenario_not_found", "Scenario not found")
    return _to_out(db, scenario)


@router.put("/scenarios/{scenario_id}", response_model=ScenarioOut)
def update_scenario(
    scenario_id: int,
    body: ScenarioIn,
    db: Session = Depends(get_db),
    _operator: str = Depends(require_operator),
):
    scenario = db.get(Scenario, scenario_id)
    if not scenario or scenario.archived:
        raise ApiError(404, "scenario_not_found", "Scenario not found")
    scenario.name = body.name
    scenario.horizon = body.horizon
    scenario.forecast = body.forecast.model_dump(mode="json")
    scenario.maintenance = [m.model_dump(mode="json") for m in body.maintenance]
    scenario.operating_parameters = body.operating_parameters.model_dump(mode="json")
    scenario.is_baseline = body.is_baseline
    db.commit()
    db.refresh(scenario)
    return _to_out(db, scenario)


@router.delete("/scenarios/{scenario_id}", status_code=204)
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    _operator: str = Depends(require_operator),
):
    scenario = db.get(Scenario, scenario_id)
    if not scenario or scenario.archived:
        raise ApiError(404, "scenario_not_found", "Scenario not found")
    scenario.archived = True
    db.commit()

from app.db.session import SessionLocal
from app.db.models import Scenario,SimulationRun
from app.devdata import main as load_devdata
from app.services.simulation import execute_run,replay_run


def test_run_survives_scenario_edits_and_replays_exactly():
    load_devdata()
    with SessionLocal() as db:
        original=db.query(Scenario).first()
        scenario=Scenario(plant_id=original.plant_id,name='Isolated provenance test',horizon=original.horizon,forecast=original.forecast,maintenance=[],operating_parameters=original.operating_parameters)
        db.add(scenario);db.commit()
        run=execute_run(db,scenario,'effluent_v1')
        snapshot=run.input_snapshot.copy()
        before=run.timeseries.copy()
        scenario.forecast={**scenario.forecast,'demand':'high'}
        scenario.archived=True
        db.commit()
        assert db.get(SimulationRun,run.id).input_snapshot==snapshot
        replay=replay_run(db,run)
        assert replay.id!=run.id and replay.timeseries==before
        assert replay.parent_run_id==run.id
        assert run.artifact_digest.startswith('sha256:')
        assert run.validation_status=='illustrative_unvalidated'


def test_failed_run_retains_inputs_without_fabricated_output(monkeypatch):
    from app.services import simulation
    class Broken:
        model_id='effluent_v1';version='broken-test'
        def run(self,inputs):raise RuntimeError('private failure')
    monkeypatch.setattr(simulation,'get_model',lambda _:Broken())
    with SessionLocal() as db:
        scenario=db.query(Scenario).first()
        run=execute_run(db,scenario,'effluent_v1')
        assert run.status=='failed' and run.input_snapshot
        assert run.kpis=={} and run.timeseries=={}
        assert run.error_code=='simulation_failed'

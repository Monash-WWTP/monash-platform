from copy import deepcopy
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.db.models import Plant, Scenario
from app.db.session import SessionLocal
from app.devdata import main as load_devdata
from app.main import app
from app.operator_auth import require_operator
from app.services.simulation import execute_run


@pytest.fixture
def comparison():
    load_devdata()
    app.dependency_overrides[require_operator] = lambda: 'test-operator'
    with SessionLocal() as db:
        scenario = db.query(Scenario).first()
        first = execute_run(db, scenario, 'effluent_v1', date(2025, 1, 1))
        second = execute_run(db, scenario, 'effluent_v1', date(2025, 1, 1))
        with TestClient(app) as client:
            yield client, db, first, second
    app.dependency_overrides.clear()


@pytest.mark.parametrize('case', [
    'duplicate', 'failed', 'running', 'plant', 'model', 'version', 'artifact',
    'empty_dates', 'different_dates', 'repeated_dates', 'short_series', 'different_metrics',
])
def test_incompatible_runs_are_rejected(comparison, case):
    client, db, first, second = comparison
    ids = [first.id, second.id]
    if case == 'duplicate':
        ids = [first.id, first.id]
    elif case in ('failed', 'running'):
        second.status = case
    elif case == 'plant':
        plant = Plant(code=f'COMPARE{second.id}', name='Other plant', latitude=3, longitude=101,
                      capacity_mld=10, description='Synthetic', status='unknown')
        db.add(plant)
        db.flush()
        scenario = Scenario(plant_id=plant.id, name='Other', horizon='3_months',
                            forecast={}, maintenance=[], operating_parameters={})
        db.add(scenario)
        db.flush()
        second.scenario_id = scenario.id
    elif case in ('model', 'version', 'artifact'):
        setattr(second, {'model': 'model_id', 'version': 'model_version', 'artifact': 'artifact_digest'}[case], 'different')
    else:
        ts = deepcopy(second.timeseries)
        if case == 'empty_dates': ts['dates'] = []
        if case == 'different_dates': ts['dates'][0] = '2024-12-31'
        if case == 'repeated_dates': ts['dates'][1] = ts['dates'][0]
        if case == 'short_series': ts['series']['bod'] = [1]
        if case == 'different_metrics': del ts['series']['bod']
        second.timeseries = ts
    db.commit()
    response = client.post('/api/v1/compare', json={'run_ids': ids})
    assert response.status_code == 422, response.text
    assert response.json()['error']['code'] == 'incompatible_runs'
    assert response.json()['error']['message']


def test_comparison_preserves_requested_run_pairing_and_input_differences(comparison):
    client, db, first, second = comparison
    snapshot = deepcopy(second.input_snapshot)
    snapshot['emission_factors']['ef_ch4'] = 0.02
    second.input_snapshot = snapshot
    db.commit()
    response = client.post('/api/v1/compare', json={'run_ids': [second.id, first.id]})
    assert response.status_code == 200, response.text
    body = response.json()
    assert [r['id'] for r in body['runs']] == [second.id, first.id]
    assert [ts['run_id'] for ts in body['timeseries']] == [second.id, first.id]
    assert body['runs'][0]['input_snapshot']['emission_factors']['ef_ch4'] == 0.02


def test_missing_runs_still_return_404(comparison):
    client, _, first, _ = comparison
    assert client.post('/api/v1/compare', json={'run_ids': [first.id, 99999999]}).status_code == 404

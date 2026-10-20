import math
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas import ScenarioIn
from app.http.errors import ApiError
from app.services.simulation import build_sim_input, input_from_snapshot


@pytest.mark.parametrize('section,field', [
    ('influent', field) for field in ('flow', 'bod', 'cod', 'tss', 'ammonia', 'tkn')
] + [('forecast', 'demand_multiplier'), ('operating_parameters', 'capacity_mld')])
@pytest.mark.parametrize('value', [-1, math.inf, -math.inf, math.nan])
def test_reject_invalid_physical_inputs(section, field, value):
    payload = {'name': 'Physical inputs'}
    if section == 'influent':
        payload['forecast'] = {'influent': {field: value}}
    else:
        payload[section] = {field: value}
    with pytest.raises(ValidationError):
        ScenarioIn.model_validate(payload)


def test_zero_concentrations_flow_and_demand_are_valid_but_capacity_must_be_positive():
    value = ScenarioIn.model_validate({'name': 'Zero input', 'forecast': {
        'influent': dict.fromkeys(('flow', 'bod', 'cod', 'tss', 'ammonia', 'tkn'), 0),
        'demand_multiplier': 0,
    }})
    assert value.forecast.influent.flow == 0
    with pytest.raises(ValidationError):
        ScenarioIn.model_validate({'name': 'Zero capacity', 'operating_parameters': {'capacity_mld': 0}})


def plant_with_limit(unit='mg/L', metric='bod'):
    return SimpleNamespace(capacity_mld=60, ef_ch4=.0121, ef_n2o=.0093,
        compliance_limits=[SimpleNamespace(metric=metric, limit_value=50, unit=unit)])


def test_reject_noncanonical_screening_units():
    scenario = SimpleNamespace(forecast={}, maintenance=[], operating_parameters={}, horizon='1_month')
    with pytest.raises(ApiError):
        build_sim_input(scenario, plant_with_limit('g/L'))


def test_normalized_unit_provenance_is_retained_in_snapshot_roundtrip():
    from dataclasses import asdict
    scenario = SimpleNamespace(forecast={}, maintenance=[], operating_parameters={}, horizon='1_month')
    inputs = build_sim_input(scenario, plant_with_limit())
    # Snapshot serialization used by persist_run must preserve the unit contract.
    snapshot = asdict(inputs)
    assert snapshot['compliance_limit_units'] == dict.fromkeys(('bod', 'cod', 'tss'), 'mg/L')
    snapshot['start_date'] = snapshot['start_date'].isoformat()
    assert input_from_snapshot(snapshot).compliance_limit_units == dict.fromkeys(('bod', 'cod', 'tss'), 'mg/L')


def test_zero_demand_multiplier_reaches_zero_flow():
    from datetime import date
    from wwtp_sim import Forecast, OperatingParameters, SimulationInput, get_model
    result = get_model('effluent_v1').run(SimulationInput(
        forecast=Forecast(demand_multiplier=0), maintenance=[],
        operating_parameters=OperatingParameters(), horizon='1_month', start_date=date(2026, 1, 1)))
    assert result.influent_flow == [0] * 30


def test_preexisting_invalid_scenario_fails_before_run():
    scenario = SimpleNamespace(forecast={'influent': {'flow': -40}}, maintenance=[],
        operating_parameters={}, horizon='1_month')
    with pytest.raises(ApiError) as error:
        build_sim_input(scenario, plant_with_limit())
    assert error.value.status_code == 422


def test_old_model_replay_fails_closed_before_execution():
    from app.services.simulation import replay_run
    original = SimpleNamespace(model_id='effluent_v1', model_version='1.4.0',
        input_snapshot={'forecast': {'demand_multiplier': 0}})
    with pytest.raises(ApiError) as error:
        replay_run(None, original)
    assert error.value.status_code == 409
    assert error.value.code == 'model_version_unavailable'


@pytest.mark.parametrize('field,value',[('capacity_mld',-1),('ef_ch4',-1),('ef_n2o',math.inf)])
def test_invalid_persisted_plant_inputs_are_rejected(field,value):
    plant=plant_with_limit();setattr(plant,field,value)
    scenario=SimpleNamespace(forecast={},maintenance=[],operating_parameters={},horizon='1_month')
    with pytest.raises(ApiError):
        build_sim_input(scenario,plant)


@pytest.mark.parametrize('field,value',[('duration_days',0),('availability_pct',-1),('availability_pct',101)])
def test_invalid_persisted_maintenance_is_rejected(field,value):
    event={'unit_type':'pump','start_date':'2026-01-01','duration_days':3,'availability_pct':50}
    event[field]=value
    scenario=SimpleNamespace(forecast={},maintenance=[event],operating_parameters={},horizon='1_month')
    with pytest.raises(ApiError) as error:
        build_sim_input(scenario,plant_with_limit())
    assert error.value.status_code==422

from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.db.platform import Account, AuditEvent, BrowserSession, now
from app.identity.dependencies import digest


@pytest.fixture(autouse=True)
def isolate_admin_rows(monkeypatch):
    """Real commits/savepoints exercise HTTP behavior; outer rollback owns all test rows."""
    import sys
    from sqlalchemy.orm import sessionmaker
    from app.db import session as database
    from app.db.session import engine
    with engine.connect() as connection:
        transaction = connection.begin()
        factory = sessionmaker(bind=connection, join_transaction_mode='create_savepoint')
        monkeypatch.setattr(database, 'SessionLocal', factory)
        monkeypatch.setattr(sys.modules[__name__], 'SessionLocal', factory)
        try:
            yield
        finally:
            transaction.rollback()


@pytest.fixture
def client():
    with TestClient(app) as value:
        yield value


def session(capabilities, mfa=True):
    token, csrf = str(uuid4()), str(uuid4())
    with SessionLocal() as db:
        account = Account(issuer='https://admin-test.invalid', subject=str(uuid4()),
            email=f'{uuid4()}@example.invalid', capabilities=capabilities)
        db.add(account); db.flush()
        db.add(BrowserSession(token_hash=digest(token), csrf_hash=digest(csrf),
            account_id=account.id, mfa_verified=mfa, expires_at=now()+timedelta(hours=1)))
        db.commit()
        return account.id, token, csrf


def use_session(client, value):
    from app.config import settings
    client.cookies.set('monash_session', value[1])
    return {'X-CSRF-Token': value[2], 'Origin': settings.web_origin}


@pytest.mark.parametrize('path', ['users','plants','stations','history','status'])
def test_admin_paths_fail_closed(client, path):
    assert client.get('/api/v1/admin/'+path).status_code == 401
    use_session(client, session(['scenario:operate']))
    assert client.get('/api/v1/admin/'+path).status_code == 403
    use_session(client, session(['platform:admin'], False))
    assert client.get('/api/v1/admin/'+path).status_code == 403


def test_admin_role_changes_atomic_revoke_and_no_elevation(client):
    actor = session(['platform:admin']); headers = use_session(client, actor)
    target = session(['report:own'])
    payload = {'capabilities':['report:own','scenario:operate'],
        'expected_capabilities':['report:own'], 'reason':'Approved operator'}
    url = '/api/v1/admin/users/'+target[0]
    assert client.patch(url, json=payload).status_code == 403
    assert client.patch(url, json={**payload, 'capabilities':['platform:admin']}, headers=headers).status_code == 422
    assert client.patch('/api/v1/admin/users/'+actor[0],json=payload,headers=headers).status_code == 403
    assert client.patch(url,json=payload,headers=headers).status_code == 200
    assert client.patch(url,json=payload,headers=headers).status_code == 409
    with SessionLocal() as db:
        assert db.get(BrowserSession,digest(target[1])) is None
        event=db.query(AuditEvent).filter_by(resource_id=target[0],action='admin.account.capabilities').one()
        assert event.actor_id == actor[0] and event.details['reason']=='Approved operator'
    listing=client.get('/api/v1/admin/users?limit=1').json()
    assert len(listing['items']) == 1 and 'subject' not in listing['items'][0]


def plant_payload():
    return {'code':'admin-'+str(uuid4()), 'name':'Admin test plant', 'latitude':3.1,
        'longitude':101.6,'capacity_mld':10,'description':'Assumed test facility',
        'stp_type':'SBR','status':'unknown','reason':'Initial approved configuration',
        'units':[{'unit_type':'pump','name':'Pump','baseline_availability':90}],
        'configuration':{'thresholds':[{'metric':'bod','value':50,'unit':'mg/L',
            'source':'Configured screening input','applicability':'Illustrative only'}],
            'emission_factors':{'ef_ch4':.0121,'ef_n2o':.0093,
                'ch4_unit':'kg CH4/kg BOD5','n2o_unit':'kg N2O-N/kg N',
                'source':'CUWA 2024 Tables5.6/5.8','applicability':'General aerobic; site applicability unverified'}}}


def test_versioned_plant_configuration_and_history(client):
    headers=use_session(client, session(['platform:admin']))
    payload=plant_payload()
    bad={**payload,'configuration':{**payload['configuration'], 'thresholds':[
        {**payload['configuration']['thresholds'][0],'unit':'g/L'}]}}
    assert client.post('/api/v1/admin/plants',json=bad,headers=headers).status_code == 422
    result=client.post('/api/v1/admin/plants',json=payload,headers=headers)
    assert result.status_code == 201, result.text
    plant=result.json(); assert plant['revision']==1
    payload['expected_revision']=1; payload['capacity_mld']=20
    changed=client.put(f"/api/v1/admin/plants/{plant['id']}",json=payload,headers=headers)
    assert changed.status_code == 200 and changed.json()['revision']==2
    assert client.put(f"/api/v1/admin/plants/{plant['id']}",json=payload,headers=headers).status_code == 409
    history=client.get('/api/v1/admin/history').json()
    assert any(x['resource_id']==str(plant['id']) for x in history['items'])
    assert 'credentials' not in client.get('/api/v1/admin/status').text


def test_station_stale_guard_preserves_source_fields(client):
    headers=use_session(client, session(['platform:admin']))
    payload={'code':'station-'+str(uuid4()),'name':'Sampling station','category':'B',
        'stp_type':'SBR','latitude':3,'longitude':101,'reason':'Metadata review'}
    created=client.post('/api/v1/admin/stations',json=payload,headers=headers)
    assert created.status_code==201, created.text
    payload['expected_revision']=created.json()['revision']; payload['name']='Reviewed station'
    url='/api/v1/admin/stations/'+payload['code']
    assert client.put(url,json=payload,headers=headers).status_code==200
    assert client.put(url,json=payload,headers=headers).status_code==409


def test_configuration_snapshot_survives_future_edits(client):
    from datetime import date
    from app.db.models import Scenario
    from app.db.platform import PlantConfigurationRevision
    from app.services.simulation import execute_run
    headers=use_session(client, session(['platform:admin']))
    payload=plant_payload()
    plant=client.post('/api/v1/admin/plants',json=payload,headers=headers).json()
    with SessionLocal() as db:
        scenario=Scenario(plant_id=plant['id'],name='Config snapshot',horizon='1_month',
            forecast={},maintenance=[],operating_parameters={})
        db.add(scenario);db.commit()
        run=execute_run(db,scenario,'effluent_v1',date(2026,1,1))
        original=run.input_snapshot
        assert original['configuration_provenance']['revision']==1
        assert original['configuration_provenance']['configuration']['emission_factors']['source'].startswith('CUWA')
        assert original['operating_parameters']['pump_availability']==90
        scenario_id=scenario.id
    payload['expected_revision']=1
    payload['configuration']['emission_factors']['ef_ch4']=.02
    assert client.put(f"/api/v1/admin/plants/{plant['id']}",json=payload,headers=headers).status_code==200
    with SessionLocal() as db:
        newer=execute_run(db,db.get(Scenario,scenario_id),'effluent_v1',date(2026,1,1))
        assert newer.input_snapshot['configuration_provenance']['revision']==2
        assert newer.input_snapshot['emission_factors']['ef_ch4']==.02
        assert original['emission_factors']['ef_ch4']==.0121
        assert db.query(PlantConfigurationRevision).filter_by(plant_id=plant['id']).count()==2


def test_admin_status_is_sanitized_and_native_list_excludes_legacy(client):
    headers=use_session(client,session(['platform:admin']))
    with SessionLocal() as db:
        legacy=Account(issuer='legacy:private-host',subject=str(uuid4()),email='legacy-secret@example.invalid')
        db.add(legacy);db.commit()
    response=client.get('/api/v1/admin/users?q=legacy-secret')
    assert response.json()['items']==[]
    status=client.get('/api/v1/admin/status')
    assert status.status_code==200,status.text
    assert set(status.json()['dependencies'].values()) <= {'ready','unavailable'}
    assert status.json()['model']['decision_use_permitted'] is False


@pytest.mark.parametrize('field,value', [('latitude',91),('longitude',181),('capacity_mld',0)])
def test_admin_plant_rejects_invalid_physical_configuration(client,field,value):
    headers=use_session(client,session(['platform:admin']))
    assert client.post('/api/v1/admin/plants',json={**plant_payload(),field:value},headers=headers).status_code==422


def test_browser_preserves_admin_grant_and_invalid_write_is_atomic(client):
    headers=use_session(client,session(['platform:admin']))
    target=session(['report:own','platform:admin'])
    response=client.patch('/api/v1/admin/users/'+target[0],headers=headers,json={
        'capabilities':['monitor:read'],'expected_capabilities':['report:own','platform:admin'],'reason':'Ordinary role update'})
    assert response.status_code==200
    assert set(response.json()['capabilities'])=={'monitor:read','platform:admin'}
    payload=plant_payload()
    saved=client.post('/api/v1/admin/plants',json=payload,headers=headers).json()
    duplicate=client.post('/api/v1/admin/plants',json=payload,headers=headers)
    assert duplicate.status_code==409
    with SessionLocal() as db:
        from app.db.platform import PlantConfigurationRevision
        assert db.query(PlantConfigurationRevision).filter_by(plant_id=saved['id']).count()==1


def test_cli_is_only_admin_grant_path():
    from app.identity.administration import set_capabilities
    target=session(['report:own'])
    with SessionLocal() as db:
        set_capabilities(db,target[0],['report:own','platform:admin'],'Trusted deployment owner','Bootstrap administrator')
        assert 'platform:admin' in db.get(Account,target[0]).capabilities
        assert db.get(BrowserSession,digest(target[1])) is None


def test_legacy_plant_view_preserves_actual_values_and_unknown_sources():
    from app.db.models import Plant, ComplianceLimit
    from app.services.admin import plant_view
    with SessionLocal() as db:
        plant=Plant(code='legacy-config-'+str(uuid4()),name='Legacy config',latitude=3,longitude=101,
            capacity_mld=8,ef_ch4=.027,ef_n2o=.008)
        plant.compliance_limits=[ComplianceLimit(metric='cod',limit_value=177,unit='mg/L')]
        db.add(plant);db.commit()
        value=plant_view(db,plant)
        assert value['revision']==0 and value['provenance_status']=='legacy_unknown'
        assert value['configuration']['emission_factors']['ef_ch4']==.027
        assert value['configuration']['emission_factors']['source']==''
        assert value['configuration']['thresholds']==[{'metric':'cod','value':177,'unit':'mg/L','source':'','applicability':''}]


def test_new_admin_station_satisfies_public_monitoring_contract(client):
    headers=use_session(client,session(['platform:admin']))
    payload={'code':'public-'+str(uuid4()),'name':'Public station','category':'B',
        'stp_type':'SBR','latitude':3,'longitude':101,'reason':'New monitoring location'}
    response=client.post('/api/v1/admin/stations',json=payload,headers=headers)
    assert response.status_code==201,response.text
    created=response.json()
    assert created['payload']['created_at']
    public=client.get('/api/v1/monitoring/stations?limit=500')
    assert public.status_code==200,public.text
    payload['expected_revision']=created['revision'];payload['name']='Updated public station'
    edited=client.put('/api/v1/admin/stations/'+payload['code'],json=payload,headers=headers)
    assert edited.status_code==200
    assert edited.json()['payload']['created_at']==created['payload']['created_at']


def test_scenario_api_preserves_omitted_plant_availability(client):
    from app.db.models import Plant, Scenario
    from app.services.simulation import build_sim_input
    headers=use_session(client,session(['platform:admin','scenario:operate']))
    plant=client.post('/api/v1/admin/plants',json=plant_payload(),headers=headers).json()
    payload={'name':'Inherit plant settings','operating_parameters':{'aeration_availability':80}}
    created=client.post(f"/api/v1/plants/{plant['id']}/scenarios",json=payload,headers=headers)
    assert created.status_code==201,created.text
    scenario=created.json()
    assert 'pump_availability' not in scenario['operating_parameters']
    updated=client.put(f"/api/v1/scenarios/{scenario['id']}",json=payload,headers=headers)
    assert updated.status_code==200,updated.text
    assert 'pump_availability' not in updated.json()['operating_parameters']
    with SessionLocal() as db:
        resolved=build_sim_input(db.get(Scenario,scenario['id']),db.get(Plant,plant['id']))
        assert resolved.operating_parameters.pump_availability==90
        assert resolved.operating_parameters.aeration_availability==80


def test_admin_rejects_single_ph_limit_until_range_semantics_exist(client):
    headers=use_session(client,session(['platform:admin']))
    payload=plant_payload()
    payload['configuration']['thresholds']=[{'metric':'ph','value':6.5,'unit':'unitless',
        'source':'Synthetic range example','applicability':'Cannot represent a pH range'}]
    assert client.post('/api/v1/admin/plants',json=payload,headers=headers).status_code==422


def test_run_snapshots_effective_fallback_thresholds(client):
    from datetime import date
    from app.db.models import Scenario
    from app.services.simulation import execute_run
    headers=use_session(client,session(['platform:admin']))
    payload=plant_payload();payload['configuration']['thresholds']=[]
    plant=client.post('/api/v1/admin/plants',json=payload,headers=headers).json()
    with SessionLocal() as db:
        scenario=Scenario(plant_id=plant['id'],name='Fallback screening',horizon='1_month',forecast={},maintenance=[],operating_parameters={})
        db.add(scenario);db.commit()
        run=execute_run(db,scenario,'effluent_v1',date(2026,1,1))
        assert run.input_snapshot['compliance_limits']=={'bod':50,'cod':200,'tss':100}
        assert run.input_snapshot['compliance_limit_units']==dict.fromkeys(('bod','cod','tss'),'mg/L')
        assert run.input_snapshot['configuration_provenance']['screening_sources']['bod']=='model_fallback_unverified'
        assert run.plant_snapshot['limits']==run.input_snapshot['compliance_limits']

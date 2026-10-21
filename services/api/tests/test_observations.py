from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.identity.dependencies import require_account
from test_reporting import account

client = TestClient(app)

def body(observation=None):
    return {'protocol_id':'citizen-observation','protocol_revision':1,
      'observation':observation or {'kind':'flooding','method':'visual','response':'unknown','surfaces':[]},
      'latitude':3.123456,'longitude':101.123456,'location_source':'selected',
      'observed_at':'2026-10-01T12:00:00Z','note':'private context'}

def test_protocol_discovery_and_context_validation():
    r=client.get('/api/v2/observation-protocols')
    assert r.status_code==200
    assert r.json()['protocol_revision']==1
    a=account(['report:own']);app.dependency_overrides[require_account]=lambda:a
    try:
      bad=[{'kind':'rainfall_accumulation','method':'instrument','value':3,'unit':'mm'},
        {'kind':'water_reading','method':'instrument','value':-1,'unit':'m','reference_kind':'depth','reference_description':'road surface'},
        {'kind':'temperature','method':'instrument','value':30,'unit':'°C'},
        {'kind':'water_appearance','method':'visual','response':'features_observed','features':[]},
        {'kind':'rain_occurrence','method':'visual','response':'normal'}]
      for obs in bad:
        assert client.post('/api/v2/observations',json=body(obs),headers={'Idempotency-Key':str(uuid4())}).status_code==422
    finally:app.dependency_overrides.clear()

def test_v2_ownership_retry_projection_and_v1_isolation():
    a=account(['report:own']);other=account(['report:own']);reviewer=account(['report:review'])
    app.dependency_overrides[require_account]=lambda:a
    try:
      payload=body();key={'Idempotency-Key':str(uuid4())}
      r=client.post('/api/v2/observations',json=payload,headers=key);assert r.status_code==201,r.text
      rid=r.json()['id']
      assert client.post('/api/v2/observations',json=payload,headers=key).json()['id']==rid
      assert client.post('/api/v2/observations',json={**payload,'note':'edited'},headers=key).status_code==409
      assert rid in [x['id'] for x in client.get('/api/v2/observations').json()['items']]
      assert rid not in [x['id'] for x in client.get('/api/v1/reports').json()['items']]
      assert client.get('/api/v1/reports/'+rid).status_code==404
      app.dependency_overrides[require_account]=lambda:other
      assert client.get('/api/v2/observations/'+rid).status_code==404
      app.dependency_overrides[require_account]=lambda:reviewer
      assert client.post('/api/v2/observations/'+rid+'/moderation',json={'status':'approved','reason':'publication review'}).status_code==200
      public=next(x for x in client.get('/api/v2/community/observations').json()['items'] if x['id']==rid)
      assert public['latitude']==3.123
      assert not {'note','media_id','owner_id','location_accuracy_m','review_reason'} & public.keys()
      assert public['observation']['response']=='unknown'
      assert rid not in [x['id'] for x in client.get('/api/v1/community/observations').json()['items']]
    finally:app.dependency_overrides.clear()

def test_quantitative_contexts_and_legacy_retry_key_collision():
    a=account(['report:own']);app.dependency_overrides[require_account]=lambda:a
    try:
      rain={'kind':'rainfall_accumulation','method':'instrument','value':0,'unit':'mm','amount_state':'value','interval_start':'2026-10-01T10:00:00Z','interval_end':'2026-10-01T12:00:00Z','gauge_type':'manual gauge','gauge_id':'test gauge'}
      for obs in [rain,{**rain,'amount_state':'trace','value':None}, {'kind':'temperature','method':'instrument','value':20,'unit':'°C','subject':'water','instrument':'thermometer','sample_context':'surface sample','calibration_status':'unknown'}]:
        r=client.post('/api/v2/observations',json=body(obs),headers={'Idempotency-Key':str(uuid4())});assert r.status_code==201,r.text
      for obs in [{**rain,'interval_start':'2026-10-02T12:00:00Z'}, {**rain,'amount_state':'trace'}, {**rain,'interval_end':'2026-10-01T12:00:00'}, {'kind':'water_reading','method':'instrument','value':-1,'unit':'m','reference_kind':'stage','reference_id':'unregistered','reference_revision':1}]:
        assert client.post('/api/v2/observations',json=body(obs),headers={'Idempotency-Key':str(uuid4())}).status_code==422
    finally:app.dependency_overrides.clear()

def test_registered_signed_stage_and_no_public_reference_identity():
    from app.db.platform import Station
    from app.db.session import SessionLocal
    reference='qa-'+str(uuid4())
    with SessionLocal() as db:
      db.add(Station(code=reference,payload={'stage_reference':{'approved':True,'revision':1,'unit':'m','label':'QA reference'}}));db.commit()
    a=account(['report:own']);app.dependency_overrides[require_account]=lambda:a
    try:
      obs={'kind':'water_reading','method':'instrument','value':-0.2,'unit':'m','reference_kind':'stage','reference_id':reference,'reference_revision':1,'instrument':'staff gauge'}
      r=client.post('/api/v2/observations',json=body(obs),headers={'Idempotency-Key':str(uuid4())});assert r.status_code==201,r.text
      page=client.get('/api/v2/observation-history').json()
      assert page['items'][0]['observation']['value']==-0.2
      assert any(x['id']==reference for x in client.get('/api/v2/observation-references').json()['items'])
    finally:app.dependency_overrides.clear()

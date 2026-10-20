"""Transactional administration with immutable evidence and optimistic edit guards."""
import hashlib
import json
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db.models import Plant, PlantUnit, ComplianceLimit
from ..db.platform import Account, AuditEvent, BrowserSession, Station, PlantConfigurationRevision, now
from ..http.errors import ApiError
from ..admin_schemas import PlantWrite, StationWrite, RoleChange


def page(query, offset, limit, encode):
    return {'items':[encode(row) for row in query.offset(offset).limit(limit)],
        'total':query.count(),'offset':offset,'limit':limit}


def account_view(account):
    return {'id':account.id,'email':account.email,'capabilities':account.capabilities,
        'created_at':account.created_at}


def users(db, offset, limit, q):
    query=db.query(Account).filter(~Account.issuer.startswith('legacy:'))
    if q:
        # Escape SQL wildcard input: search is literal and bounded.
        pattern='%'+q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
        query=query.filter(or_(Account.email.ilike(pattern,escape='\\'),Account.id.ilike(pattern,escape='\\')))
    return page(query.order_by(Account.created_at,Account.id),offset,limit,account_view)


def audit(db, actor, action, resource, reason, before, after):
    db.add(AuditEvent(actor_id=actor.id,action='admin.'+action,resource_id=str(resource),
        details={'reason':reason,'before':before,'after':after}))


def commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ApiError(409,'conflict','A conflicting record was saved; reload and try again.')


def change_roles(db, actor, account_id, body: RoleChange):
    if account_id == actor.id:
        raise ApiError(403,'self_edit_forbidden','Use another authorized administrator for permission changes.')
    target=db.query(Account).filter_by(id=account_id).with_for_update().first()
    if not target or target.issuer.startswith('legacy:'):
        raise ApiError(404,'account_not_found','Native account not found')
    if set(body.expected_capabilities) != set(target.capabilities):
        raise ApiError(409,'stale_edit','Permissions changed; reload before editing.')
    before=list(target.capabilities)
    # Browser changes never grant or revoke administration.
    target.capabilities=sorted(set(body.capabilities) | ({'platform:admin'} if 'platform:admin' in before else set()))
    db.query(BrowserSession).filter_by(account_id=target.id).delete()
    audit(db,actor,'account.capabilities',target.id,body.reason,before,target.capabilities)
    commit(db)
    return account_view(target)


def latest_configuration(db, plant_id):
    return db.query(PlantConfigurationRevision).filter_by(plant_id=plant_id).order_by(PlantConfigurationRevision.version.desc()).first()


def plant_view(db, plant):
    latest=latest_configuration(db,plant.id)
    return {**{key:getattr(plant,key) for key in ('id','code','name','latitude','longitude','capacity_mld','description','stp_type','status')},
        'revision':latest.version if latest else 0,
        'units':[{'unit_type':u.unit_type,'name':u.name,'baseline_availability':u.baseline_availability} for u in plant.units],
        'configuration':latest.payload['configuration'] if latest else {
            'thresholds':[{'metric':t.metric,'value':t.limit_value,'unit':t.unit,'source':'','applicability':''}
                          for t in plant.compliance_limits],
            'emission_factors':{'ef_ch4':plant.ef_ch4,'ef_n2o':plant.ef_n2o,
                'ch4_unit':'kg CH4/kg BOD5','n2o_unit':'kg N2O-N/kg N','source':'','applicability':''}},
        'provenance_status':'supplied_unverified' if latest else 'legacy_unknown'}


def plants(db, offset, limit):
    return page(db.query(Plant).order_by(Plant.id),offset,limit,lambda p:plant_view(db,p))


def save_plant(db: Session, actor, body: PlantWrite, plant_id=None):
    plant=db.query(Plant).filter_by(id=plant_id).with_for_update().first() if plant_id is not None else None
    if plant_id is not None and plant is None:
        raise ApiError(404,'plant_not_found','Plant not found')
    latest=latest_configuration(db,plant.id) if plant else None
    version=latest.version if latest else 0
    if body.expected_revision != version:
        raise ApiError(409,'stale_edit','Plant configuration changed; reload before saving.')
    before=plant_view(db,plant) if plant else None
    if plant is None:
        plant=Plant();db.add(plant)
    for key in ('code','name','latitude','longitude','capacity_mld','description','stp_type','status'):
        setattr(plant,key,getattr(body,key))
    factors=body.configuration.emission_factors
    plant.ef_ch4=factors.ef_ch4;plant.ef_n2o=factors.ef_n2o
    plant.units=[PlantUnit(**u.model_dump()) for u in body.units]
    plant.compliance_limits=[ComplianceLimit(metric=t.metric,limit_value=t.value,unit=t.unit) for t in body.configuration.thresholds]
    payload=body.model_dump(exclude={'reason','expected_revision'})
    payload['provenance_status']='supplied_unverified'
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise ApiError(409,'conflict','Plant code is already in use.')
    db.add(PlantConfigurationRevision(plant_id=plant.id,version=version+1,actor_id=actor.id,
        reason=body.reason,payload=payload))
    audit(db,actor,'plant.configuration',plant.id,body.reason,before,payload)
    commit(db)
    return plant_view(db,plant)


def station_revision(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def station_view(station):
    return {'code':station.code,'payload':station.payload,'revision':station_revision(station.payload)}


def stations(db,offset,limit):
    return page(db.query(Station).order_by(Station.code),offset,limit,station_view)


def save_station(db,actor,body:StationWrite,code=None):
    station=db.query(Station).filter_by(code=code).with_for_update().first() if code is not None else None
    if code is not None and station is None:
        raise ApiError(404,'station_not_found','Station not found')
    if code is not None and body.code != code:
        raise ApiError(422,'immutable_station_code','Station codes cannot change after creation.')
    if station and body.expected_revision != station_revision(station.payload):
        raise ApiError(409,'stale_edit','Station changed; reload before saving.')
    if not station and body.expected_revision is not None:
        raise ApiError(409,'stale_edit','New stations do not have an existing revision.')
    before=station.payload.copy() if station else None
    fields=body.model_dump(exclude={'expected_revision','reason'})
    if station:
        station.payload={**station.payload,**fields}
    else:
        station=Station(code=body.code,payload={**fields,'created_at':now().isoformat()});db.add(station)
    audit(db,actor,'station.metadata',body.code,body.reason,before,station.payload)
    commit(db)
    return station_view(station)


def history(db,offset,limit):
    # Only administrative events; never report payloads, identity proofs or session material.
    query=db.query(AuditEvent).filter(AuditEvent.action.in_(
        ['admin.account.capabilities','admin.plant.configuration','admin.station.metadata','account.capabilities']))
    def encode(event):
        return {'id':event.id,'actor_id':event.actor_id,'action':event.action,
            'resource_id':event.resource_id,'created_at':event.created_at,
            'details':{k:event.details[k] for k in ('reason','before','after') if k in event.details}}
    return page(query.order_by(AuditEvent.created_at.desc(),AuditEvent.id),offset,limit,encode)


def status():
    from ..config import settings
    from ..routers import readiness
    from wwtp_sim import get_model
    dependencies={}
    checks={'database':(True,readiness.check_database),
        'storage':(bool(settings.storage_endpoint),readiness.check_storage),
        'identity':(bool(settings.oidc_jwks_url),readiness.check_identity)}
    for name,(configured,check) in checks.items():
        try:
            if not configured:raise ValueError('Not configured')
            check();dependencies[name]='ready'
        except Exception:
            dependencies[name]='unavailable'
    model=get_model('effluent_v1')
    return {'environment':settings.app_env,'dependencies':dependencies,
        'model':{'id':model.model_id,'version':model.version,'validation_status':'illustrative_unvalidated','decision_use_permitted':False},
        'release_acceptance':'pending_external_acceptance'}

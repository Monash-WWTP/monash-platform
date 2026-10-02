"""Owner reports and scoped media; moderation never exposes raw private reports publicly."""
import hashlib
import json
from io import BytesIO
from uuid import uuid4
from fastapi import APIRouter,Depends,Header,Query,UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from PIL import Image,UnidentifiedImageError
from ..db.session import get_db
from ..db.platform import CitizenReport,Media,AuditEvent,Account
from ..identity.dependencies import require_account,require_citizen,require_reviewer
from ..http.errors import ApiError
from ..reporting.schemas import ReportInput,ModerationInput
from ..reporting import storage
from ..config import settings

router=APIRouter(tags=['citizen reports'])


def own_projection(report):
    return {**report.payload,'id':report.id,'media_id':report.media_id,
            'moderation_status':report.status,'created_at':report.created_at.isoformat()}


@router.post('/reports',status_code=201)
def submit(body:ReportInput,idempotency_key:str=Header(min_length=8,max_length=128),
           account:Account=Depends(require_citizen),db:Session=Depends(get_db)):
    payload=body.model_dump(mode='json')
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    previous=db.query(CitizenReport).filter_by(owner_id=account.id,idempotency_key=idempotency_key).first()
    if previous:
        if previous.payload_hash!=digest:raise ApiError(409,'idempotency_conflict','This retry key was used for different report content')
        return own_projection(previous)
    if body.media_id:
        media=db.get(Media,body.media_id)
        if not media or media.owner_id!=account.id:raise ApiError(404,'media_not_found','Photo not found')
    report=CitizenReport(owner_id=account.id,idempotency_key=idempotency_key,payload_hash=digest,
                         category=body.category,latitude=body.latitude,longitude=body.longitude,
                         payload=payload,media_id=body.media_id)
    db.add(report)
    try:db.commit()
    except IntegrityError:
        db.rollback()
        previous=db.query(CitizenReport).filter_by(owner_id=account.id,idempotency_key=idempotency_key).first()
        if not previous or previous.payload_hash!=digest:raise ApiError(409,'idempotency_conflict','Submission could not be reconciled')
        return own_projection(previous)
    return own_projection(report)


@router.get('/reports')
def history(offset:int=Query(0,ge=0),limit:int=Query(100,ge=1,le=500),
            account:Account=Depends(require_citizen),db:Session=Depends(get_db)):
    query=db.query(CitizenReport).filter_by(owner_id=account.id)
    return {'items':[own_projection(r) for r in query.order_by(CitizenReport.created_at.desc()).offset(offset).limit(limit)],
            'total':query.count(),'offset':offset,'limit':limit}


@router.get('/reports/{report_id}')
def report_detail(report_id:str,account:Account=Depends(require_account),db:Session=Depends(get_db)):
    report=db.get(CitizenReport,report_id)
    if not report or (report.owner_id!=account.id and 'report:review' not in account.capabilities):
        raise ApiError(404,'report_not_found','Report not found')
    return own_projection(report)


@router.get('/moderation/reports')
def moderation_queue(offset:int=Query(0,ge=0),limit:int=Query(100,ge=1,le=500),
                     account:Account=Depends(require_reviewer),db:Session=Depends(get_db)):
    query=db.query(CitizenReport).filter_by(status='pending')
    return {'items':[own_projection(r) for r in query.order_by(CitizenReport.created_at).offset(offset).limit(limit)],
            'total':query.count(),'offset':offset,'limit':limit}


@router.post('/reports/{report_id}/moderation')
def moderate(report_id:str,body:ModerationInput,account:Account=Depends(require_reviewer),db:Session=Depends(get_db)):
    report=db.query(CitizenReport).filter_by(id=report_id).with_for_update().first()
    if not report:raise ApiError(404,'report_not_found','Report not found')
    before=report.status
    report.status=body.status
    db.add(AuditEvent(actor_id=account.id,action='report.moderate',resource_id=report.id,
                      details={'before':before,'after':body.status,'reason':body.reason}))
    db.commit()
    return own_projection(report)


@router.get('/community/observations')
def community(category:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(100,ge=1,le=500),db:Session=Depends(get_db)):
    query=db.query(CitizenReport).filter_by(status='approved')
    if category:query=query.filter_by(category=category)
    # Explicit allowlist; never expose private free text, identities, original coordinates or media.
    result=[]
    for r in query.order_by(CitizenReport.created_at.desc()).offset(offset).limit(limit):
        result.append({'id':r.id,'category':r.category,'condition':r.payload.get('condition'),
            'reading_value':r.payload.get('reading_value'),'reading_unit':r.payload.get('reading_unit'),
            'latitude':round(r.latitude,3),'longitude':round(r.longitude,3),'location_precision':'rounded_0.001_degree',
            'observed_at':r.payload.get('observed_at'),'created_at':r.created_at.isoformat()})
    return {'items':result,'total':query.count(),'offset':offset,'limit':limit}


@router.post('/media',status_code=201)
async def upload(file:UploadFile,account:Account=Depends(require_citizen),db:Session=Depends(get_db)):
    content=await file.read(10*1024*1024+1)
    if not content or len(content)>10*1024*1024:raise ApiError(413,'photo_too_large','Photo must be between 1 byte and 10 MB')
    try:
        image=Image.open(BytesIO(content))
        if image.format not in {'JPEG','PNG','WEBP'} or image.width*image.height>25_000_000:
            raise ValueError('Unsupported photo')
        mime={'JPEG':'image/jpeg','PNG':'image/png','WEBP':'image/webp'}[image.format]
        image.verify()
    except (UnidentifiedImageError,ValueError,OSError,Image.DecompressionBombError):
        raise ApiError(422,'invalid_photo','Use a valid JPEG, PNG or WebP photo up to 25 megapixels')
    key=account.id+'/'+str(uuid4())
    try:
        store=storage.client()
        store.put_object(Bucket=settings.storage_bucket,Key=key,Body=content,ContentType=mime)
    except Exception:raise ApiError(503,'storage_unavailable','Photo storage is unavailable; photo was not confirmed')
    media=Media(owner_id=account.id,object_key=key,sha256=hashlib.sha256(content).hexdigest(),byte_size=len(content),mime=mime)
    db.add(media)
    try:db.commit()
    except Exception:
        db.rollback()
        store.delete_object(Bucket=settings.storage_bucket,Key=key)
        raise
    return {'id':media.id,'sha256':media.sha256,'byte_size':media.byte_size,'mime':media.mime}


@router.get('/media/{media_id}')
def download(media_id:str,account:Account=Depends(require_account),db:Session=Depends(get_db)):
    media=db.get(Media,media_id)
    reviewable='report:review' in account.capabilities and db.query(CitizenReport).filter_by(media_id=media_id).first()
    if not media or (media.owner_id!=account.id and not reviewable):raise ApiError(404,'media_not_found','Photo not found')
    try:
        value=storage.client().get_object(Bucket=settings.storage_bucket,Key=media.object_key)['Body'].read(media.byte_size+1)
        if len(value)!=media.byte_size or hashlib.sha256(value).hexdigest()!=media.sha256:raise ValueError('Integrity mismatch')
    except Exception:raise ApiError(503,'storage_unavailable','Photo storage is unavailable')
    return Response(value,media_type=media.mime,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

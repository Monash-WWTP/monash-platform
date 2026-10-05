"""Limited legacy ownership handover; original subject proof, never email matching."""
from uuid import UUID
import httpx
from fastapi import APIRouter,Depends
from pydantic import BaseModel,ConfigDict,SecretStr,Field
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.platform import Account,CitizenReport,Media,AuditEvent
from ..identity.dependencies import require_citizen
from ..config import settings
from ..http.errors import ApiError
router=APIRouter(prefix='/migration',tags=['legacy migration'])
class ClaimInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    legacy_access_token:SecretStr=Field(min_length=8,max_length=9000)
class ClaimOutput(BaseModel):
    claimed:int


def legacy_subject(token:str)->str:
    try:
        response=httpx.get(settings.supabase_url.rstrip('/')+'/auth/v1/user',headers={
            'apikey':settings.supabase_key,'Authorization':'Bearer '+token},timeout=5)
    except httpx.HTTPError:raise ApiError(503,'legacy_identity_unavailable','Original identity service is unavailable')
    if response.status_code in {401,403}:raise ApiError(401,'legacy_proof_invalid','Original account proof is invalid or expired')
    if not response.is_success:raise ApiError(503,'legacy_identity_unavailable','Original identity service is unavailable')
    try:return str(UUID(response.json()['id']))
    except (ValueError,KeyError):raise ApiError(401,'legacy_proof_invalid','Original identity proof is invalid')


@router.post('/claim-reports',response_model=ClaimOutput)
def claim(body:ClaimInput,account:Account=Depends(require_citizen),db:Session=Depends(get_db)):
    subject=legacy_subject(body.legacy_access_token.get_secret_value())
    reports=db.query(CitizenReport).filter_by(legacy_subject=subject,owner_id=None).with_for_update().all()
    for report in reports:
        if report.media_id:
            media=db.get(Media,report.media_id);custodian=db.get(Account,media.owner_id) if media else None
            if not custodian or custodian.issuer!='legacy:'+settings.supabase_url or custodian.subject!=subject:
                raise ApiError(409,'migration_custody_conflict','Source photo custody requires administrator reconciliation')
            media.owner_id=account.id
        report.owner_id=account.id
        db.add(AuditEvent(actor_id=account.id,action='report.claim',resource_id=report.id,details={
            'proof':'original_subject_verified','source':settings.supabase_url}))
    db.commit()
    return {'claimed':len(reports)}
